import os.path
import csv, glob, sys, string, math, datetime, re, locale, timeit, logging

from django import forms
from django.template import RequestContext
from django.core.urlresolvers import reverse
from django.core.cache import cache
from django.http import HttpResponseRedirect, Http404, HttpResponseBadRequest, HttpResponse
from django.shortcuts import render_to_response, get_object_or_404, redirect, render
from django.contrib import messages
from django.db.models import Q, Avg, Max, Min, Count, StdDev, Variance
from django.core.files.uploadhandler import MemoryFileUploadHandler
from django.utils import simplejson
from django.template import Template, Context
from django.forms.formsets import formset_factory
import django_tables2 as tables

from marketanalyzer.models import *

logging.basicConfig()

# TO DO: validate all forms/input

# how kosher is this? (placement, usage of a global at all, etc)
uploadPath = '/home/django/upload/'

# convert dumper's timestamp to a python datetime object
def convTS(ts):
    # dumper TS is the number of 100-nanosecond intervals since Jan. 1, 1600
    # we convert here to a 32-bit representation of seconds since 1-1-1970
    # and then return a datetime object representing that
    return datetime.datetime.fromtimestamp(((int(ts) - 116444736000000000) /
                                             10000000))

# convert strings representing bools in export files to real boolean vals
# (for use with CSV exports)
def str2bool(val):
    if ( val == 'True' ):
        return True
    if ( val == 'False' ):
        return False

class UploadFileForm(forms.Form):
    file  = forms.FileField()

# accept an upload with market data
def upload(request):
    if request.method == 'POST':
        print '** POST method determined.'
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            print '** Form validated.'
            handle_uploaded_file(request.FILES['file'])
            messages.add_message(request, messages.SUCCESS,
                                 'File uploaded successfully!')
            return HttpResponseRedirect(reverse('marketanalyzer.views.upload'))
        else:
            messages.add_message(request, messages.ERROR, 'Upload failed!')
            print '!! Invalid form. Errors:', form.errors
    else:
        print '!! No POST'
        form = UploadFileForm()
        
    # last arg is b/c of CSRF
    return render_to_response('records/upload.html', {'form': form},
                              context_instance=RequestContext(request))

# !! Dev server isn't multithreaded, so won't see progress update requests while
# receiving the file. Even when using an MT patch (threadedmanage.py) to run it
# this functionality requires other things that are best left for a linux
# apache server.

# view to present upload progress to AJAX
def upload_progress(request):
    """
    Return JSON object with information about the progress of an upload.
    """
    print "** IN upload_progress."
    progress_id = None
    if 'X-Progress-ID' in request.GET:
        print "** X-Progress-ID seen in request.GET"
        progress_id = request.GET['X-Progress-ID']
    elif 'X-Progress-ID' in request.META:
        print "** X-Progress-ID seen in request.META"
        progress_id = request.META['X-Progress-ID']
    if progress_id:
        print "** progress_id seen"
        from django.utils import simplejson
        cache_key = "%s_%s" % (request.META['REMOTE_ADDR'], progress_id)
        data = cache.get(cache_key)
        json = simplejson.dumps(data)
        return HttpResponse(json)
    else:
        return HttpResponseBadRequest('Server Error: You must provide X-Progress-ID header or query param.')

# write contents of an uploaded file to server's drive and then call insertion
# method
# TO DO: -delete uploaded files after X time has passed?
#        -rename new file if filename in use?
#        --tie into uniqueness check on orders?
def handle_uploaded_file(f):
    path = uploadPath + f.name  # uploadPath is defined above as a global
    #if ( not(os.path.isfile(path))):     # if file doesn't exist already
    #   print "** File does not already exist:", path
    destination = open(path, 'wb')
    for chunk in f.chunks():
        destination.write(chunk)
    destination.close()
    print "** Inserting data to DB."
    insert_to_db(path)
    print "** Done inserting data to DB."
    #else:
    #    print "!! Aborting due to file already existing:", path

# insert a file on the server containing market data (dumper format) into
# the DB
# TO DO: handle problem of multiple people uploading data on same order
#        -consider checking orderID, if matches, check order contents,
#          and if they match, then don't add order
def insert_to_db(f):
    print '========== insert_to_db =========='
    # keyList used to zip()
    keyList = ['lastUpdated', 'price', 'volRemaining', 'typeID', 'range',
               'orderID', 'volEntered', 'minVolume', 'bid', 'issueDate',
               'duration', 'stationID', 'jumps']
    expList = []
    types = set()
    timestamp = -1
    
    with open(f, 'rb') as f:
        reader = csv.reader(f)
        # wierd shit can happen here so we should catch errors
        try:
            for row in reader:
                # if this isn't a blank line
                if ( len(row) ):    
                    # if row starts with 'TS:' we know it's a timestamp line
                    if ( string.find(row[0], 'TS:') == 0 ):
                        # extract UTC timestamp (datetime.utcnow())
                        timestamp = row[0][4:]
                    # if this isn't a keys row, it must be data
                    elif ( not(string.find(row[0], 'price') == 0) ):
                        # insert the timestamp at front of the list
                        #  (as per keyList)
                        row.insert(0, timestamp)
                        # add entry to expList
                        expList.append(dict(zip(keyList, row)))
                        
        except csv.Error, e:
            sys.exit('file %s, line %d: %s' % (filename, reader.line_num, e))
            
    f.close()
    lastType = -1
    
    # expList now contains a list of dicts, where each dict is a row from the
    # market dump source
    for i in expList:
        #print '** i:', i
        # print out typeID only when it changes
        if ( lastType != i['typeID'] ):
            lastType = i['typeID']
            print '** inserting typeID:', lastType
        
        # TO DO: consider putting types.add() inside of the try/except block so
        # we don't pass types to compute_price_data that it can't work with
        # (currently, we are checking for the same errors in compute_price_data
        # as we are here)
        
        # add type as seen, so we can limit our market computations to
        # item types that exist in the newly added records
        types.add(i['typeID'])
        
        try:
            r = MarketRecord(typeID=invTypes.objects.get(pk=i['typeID']),
                             volEntered=i['volEntered'],
                             minVolume=i['minVolume'],
                             jumps=i['jumps'],
                             lastUpdated=i['lastUpdated'],
                             price=i['price'],
                             stationID=staStations.objects.get(pk=i['stationID']),
                             range=i['range'],
                             orderID=i['orderID'],
                             issueDate=i['issueDate'],
                             volRemaining=i['volRemaining'],
                             duration=i['duration'],
                             bid=str2bool(i['bid']))
        # haven't ever actually seen this raised yet; ok to remove?
        except MarketRecord.DoesNotExist as detail:
            print '!! MarketRecord does not exist (is it a new item?):', detail
            continue
        except Exception as detail:
            print '!! ERROR in insert_to_db (is it a new item?) [typeID:', i['typeID'], ']:', detail
            continue
        else:
            r.save()

    #print '** types:', types
    compute_price_data(types)

# expects a set of typeIDs whose stats need to be computed
def compute_price_data(types):
    print '========== compute_price_data =========='
        
    
    for t in types:
        print '** Computing for type:', t
        
        buyPriceList = []
        sellPriceList = []
        bLen = -1
        sLen = -1
        
        try:
            # store query results now, in case they change during computation
            item = invTypes.objects.get(typeID=t)
        except invTypes.DoesNotExist as detail:
            print '!! `item` not found in query:', detail
            continue
        else:
            buyOrders = item.marketrecord_set.filter(bid=True)
            sellOrders = item.marketrecord_set.filter(bid=False)
            
            item.meanSellPrice = sellOrders.aggregate(Avg('price')).values()[0]
            item.highSellPrice = sellOrders.aggregate(Max('price')).values()[0]
            item.lowSellPrice = sellOrders.aggregate(Min('price')).values()[0]
            item.stdDevSell = sellOrders.aggregate(StdDev('price')).values()[0]
            item.varianceSell = sellOrders.aggregate(Variance('price')).values()[0]
            
            item.meanBuyPrice = buyOrders.aggregate(Avg('price')).values()[0]
            item.highBuyPrice = buyOrders.aggregate(Max('price')).values()[0]
            item.lowBuyPrice = buyOrders.aggregate(Min('price')).values()[0]
            item.stdDevBuy = buyOrders.aggregate(StdDev('price')).values()[0]
            item.varianceBuy = buyOrders.aggregate(Variance('price')).values()[0]
            
    
            # setup stuff for finding medians
            for rec in buyOrders:
                buyPriceList.append(rec.price)
                
            for rec in sellOrders:
                sellPriceList.append(rec.price)
                
            bLen = len(buyPriceList)
            sLen = len(sellPriceList)
            
            #print '** len(buyPriceList):', bLen
            #print '** len(sellPriceList):', sLen
            
            # calculate medians
            if bLen == 0:
                pass
            elif bLen % 2 != 0:   # odd amt of items
                item.medianBuyPrice = buyPriceList[bLen/2]
            else:   # even amt of items, so avg 2 middle items' values
                item.medianBuyPrice = (buyPriceList[int(math.ceil(bLen)/2)]
                                       + buyPriceList[int(math.floor(bLen)/2)]
                                       / 2)
            if sLen == 0:
                pass
            elif sLen % 2 != 0:
                item.medianSellPrice = sellPriceList[sLen/2]
            else:
                item.medianSellPrice = (sellPriceList[int(math.ceil(sLen)/2)]
                                       + sellPriceList[int(math.floor(sLen)/2)]
                                       / 2)
                
            item.save()
            
            # FOR DEV PURPOSES ONLY, this speeds up db_clear
            x = modified(typeID=item.typeID)
            x.save()

# table to contain market records of (potentially) multiple types
class RecordTable(tables.Table):
    # since MarketRecord doesn't directly hold typeName, we must override the
    #  accessor to follow the FK to get it
    type_name = tables.Column(accessor='typeID.typeName')
    regionName = tables.Column(accessor='stationID.regionID.regionName')
    #solarSystemName = tables.Column(accessor='solarSystemID.solarSystemName',
    #                                verbose_name='Solar System')
    security = tables.Column(accessor='stationID.solarSystemID.security')
    stationName = tables.Column(accessor='stationID.stationName')
    
    # TO DO: -remove fields from models so we don't have to hide so much
    #        -hide itemName col from detail views
    #        -get price to align right and force 2 decimal places shown
    id = tables.Column(visible=False)
    typeID = tables.Column(visible=False)
    range = tables.Column(visible=False)
    orderID = tables.Column(visible=False)
    #regionID = tables.Column(visible=False)
    #solarSystemID = tables.Column(visible=False)
    jumps = tables.Column(visible=False)
    bid = tables.Column(visible=False)
    minVolume = tables.Column(visible=False)
    solarSystemName = tables.Column(visible=False)
    stationID = tables.Column(visible=False)
    
    def render_price(self, value):
        return '%s' % locale.format('%.2f', value, grouping=True)
        
    def render_security(self, value):
        return '%.1f' % value
    
    # django-tables2 offers automatic generation of columns based on a model
    # NOTE: Col sorting is handled by the DB when table is backed by a model
    class Meta:
        model = MarketRecord
        attrs = {'class': 'paleblue'}
        sequence = ('security', 'regionName', 'stationName',
                    'type_name', 'price', 'volEntered', 'volRemaining', '...')

# table of order info for the type_detail view
class DetailTable(RecordTable):
    regionName = tables.Column(accessor='stationID.regionID.regionName')
    solarSystemName = tables.Column(accessor='stationID.solarSystemID.solarSystemName',
                                    verbose_name='Solar System')
    security = tables.Column(accessor='stationID.solarSystemID.security')
    stationName = tables.Column(accessor='stationID.stationName')
    id = tables.Column(visible=False)
    typeID = tables.Column(visible=False)
    range = tables.Column(visible=False)
    orderID = tables.Column(visible=False)
    #regionID = tables.Column(visible=False)
    #solarSystemID = tables.Column(visible=False)
    jumps = tables.Column(visible=False)
    bid = tables.Column(visible=False)
    type_name = tables.Column(visible=False)
    minVolume = tables.Column(visible=False)
    solarSystemName = tables.Column(visible=False)
    stationID = tables.Column(visible=False)
    
    class Meta:
        model = MarketRecord
        attrs = {'class': 'paleblue'}
        sequence = ('security', 'regionName', 'stationName',
                    'type_name', 'price', 'volEntered', 'volRemaining', '...')
        
# TO DO: for all views using tables
#        -remove some irrelevant columns from tables
#        -paginate results
#        -combine the all* views into one
#        -humanize data (add commas to large numbers, etc)

# provides buy and sell tables of all market orders of a single item type
def type_detail(request, type_id):
    try:
        item = invTypes.objects.get(pk=type_id)
    except invTypes.DoesNotExist:
        raise Http404   # perhaps display a more informative page
    
    # Dict to hold the attributes of the item in question
    attrs = {}
    
    # Fill dict with attribute names as keys, and the int/float as values
    # Each attribute should have either an int or a float value, not both
    for x in dgmTypeAttributes.objects.filter(typeID=item.typeID):
        if x.valueInt:
            attrs[x.attributeID.attributeName] = x.valueInt
        else:
            attrs[x.attributeID.attributeName] = x.valueFloat
        
    #print '** attrs:', attrs.items()
        
    buy = None
    sell = None
    
    # by default, sort buy orders by descending price
    if ( request.GET.get('b-sort') ):
        bOrder = request.GET.get('b-sort')
    else:
        bOrder = '-price'
    
    # by default, sort sell by ascending price
    if ( request.GET.get('s-sort') ):
        sOrder = request.GET.get('s-sort')
    else:
        sOrder = 'price'
        
    buy = DetailTable(item.marketrecord_set.filter(bid__exact=1),
                        prefix='b-', order_by=bOrder)
    
    sell = DetailTable(item.marketrecord_set.filter(bid__exact=0),
                        prefix='s-', order_by=sOrder)
    
    return render_to_response('records/type_detail.html',
                              { 'buy': buy, 'sell': sell, 'item': item,
                               'attrs': attrs },
                              context_instance=RequestContext(request))

# show every buy order in the DB
def all_buy(request):
    # by default, sort by descending price
    if ( request.GET.get('sort') ):
        order = request.GET.get('sort')
    else:
        order = '-price'
    # get just the BUY orders
    table = RecordTable(MarketRecord.objects.filter(bid__exact=1),
                        order_by=order)
    return render_to_response('records/all_buy.html', {'table': table},
                              context_instance=RequestContext(request))

# show every sell order in the DB
def all_sell(request):
    # by default, sort by ascending price
    if ( request.GET.get('sort') ):
        order = request.GET.get('sort')
    else:
        order = 'price'
    
    # get just the SELL orders
    table = RecordTable(MarketRecord.objects.filter(bid__exact=0),
                        order_by=order)
    return render_to_response('records/all_sell.html', {'table': table},
                              context_instance=RequestContext(request))

# probably won't regularly use the "all" view, and paginating requires more work
# with multiple tables so hold off?

# show ALL orders in the DB
def all(request):
    # by default, sort buy orders by descending price
    if ( request.GET.get('b-sort') ):
        bOrder = request.GET.get('b-sort')
    else:
        bOrder = '-price'
    
    # by default, sort sell by ascending price
    if ( request.GET.get('s-sort') ):
        sOrder = request.GET.get('s-sort')
    else:
        sOrder = 'price'
        
    buy = RecordTable(MarketRecord.objects.filter(bid__exact=1),
                      prefix='b-', order_by=bOrder)
    sell = RecordTable(MarketRecord.objects.filter(bid__exact=0),
                       prefix='s-', order_by=sOrder)
        
    return render_to_response('records/all.html', {'buy': buy, 'sell': sell},
                              context_instance=RequestContext(request))

# Remove all marketrecords from DB and clear associated invType statistics
# regarding price.
# TO DO: This is slow b/c of the invType work, consider tracking types that
#        have had their *price fields edited.
#        May be a waste of time since this will rarely be run in production env.
def clear_db(request):
    if request.method == 'POST':
        MarketRecord.objects.all().delete()
        
        # only have to reset stats for types that we've modified
        for type in modified.objects.all():
            item = invTypes.objects.get(typeID=type.typeID)
            print '** Clearing stats for:', item.typeName
            
            #for i in query:
            item.medianSellPrice = None
            item.medianBuyPrice = None
            item.meanSellPrice = None
            item.meanBuyPrice = None
            item.lowSellPrice = None
            item.highSellPrice = None
            item.lowBuyPrice = None
            item.highBuyPrice = None
            item.stdDev = None
            item.variance = None
            item.save()
                
        modified.objects.all().delete()
        messages.add_message(request, messages.SUCCESS,
                             'All orders and associated stats have been erased!')
    return render_to_response('records/clear_db.html',
                              context_instance=RequestContext(request))
    
def clear_lp_db(request):
    if request.method == 'POST':
        LPReward.objects.all().delete()
        
        # reset isLPreward for all invTypes
        for type in invTypes.objects.all():
            
            #value = type.typeName
            #try:
            #    unicode(value, "utf-8")
            #except UnicodeError:
            #    value = unicode(value, "utf-8")
            #else:
            #    # value was valid ASCII data
            #    pass
            
            try:
                print '** Clearing isLPreward for:', type.typeName
            except UnicodeEncodeError as e:
                print '!! Weird character(s) in name: ', e
            type.isLPreward = False
            type.save()
                
        messages.add_message(request, messages.SUCCESS,
                             'All LP rewards and isLPreward attrs have been cleared!')
    return render_to_response('records/clear_lp_db.html',
                              context_instance=RequestContext(request))

# related to search view
def normalize_query(query_string,
                    findterms=re.compile(r'"([^"]+)"|(\S+)').findall,
                    normspace=re.compile(r'\s{2,}').sub):
    ''' Splits the query string in invidual keywords, getting rid of unecessary spaces
        and grouping quoted words together.
        Example:
        
        >>> normalize_query('  some random  words "with   quotes  " and   spaces')
        ['some', 'random', 'words', 'with quotes', 'and', 'spaces']
    '''
    return [normspace(' ', (t[0] or t[1]).strip()) for t in
            findterms(query_string)] 

# related to search view
def get_query(query_string, search_fields):
    ''' Returns a query, that is a combination of Q objects. That combination
        aims to search keywords within a model by testing the given search fields.
    '''
    query = None # Query to search for every search term        
    terms = normalize_query(query_string)
    for term in terms:
        or_query = None # Query to search for a given term in each field
        for field_name in search_fields:
            q = Q(**{"%s__icontains" % field_name: term})
            if or_query is None:
                or_query = q
            else:
                or_query = or_query | q
        if query is None:
            query = or_query
        else:
            query = query & or_query
    return query

# view to search by item name, provides template with a list of matching items
def search(request):
    #print '** sellable:', sellable
    #print '========= SEARCH ========='
    #print '** REQUEST:', request
    #print '** GET:', request.GET
    query_string = ''
    found_entries = None
    if ('q' in request.GET) and request.GET['q'].strip():
        query_string = request.GET['q']
        
        # pick what field to search here
        entry_query = get_query(query_string, ['typeName',])
        
        found_entries=invTypes.objects.filter(entry_query).exclude(
            marketGroupID=None).order_by('typeName')

    return render_to_response('records/search.html',
                              { 'query_string': query_string,
                               'found_entries': found_entries },
                              context_instance=RequestContext(request))
    
class LPResults(tables.Table):
    corp = tables.Column(verbose_name='Corporation')
    itemName = tables.Column(verbose_name='Item')
    qty = tables.Column(verbose_name='Qty')
    ISKcost = tables.Column(verbose_name='ISK Cost')
    LPcost = tables.Column(verbose_name='LP Cost')
    
    class Meta:
        attrs = {'class': 'paleblue'}
    
def lp_search(request):
    query_string = ''
    found_entries = None
    results = ''
    
    if ('q' in request.GET) and request.GET['q'].strip():
        query_string = request.GET['q']
        
        # pick what field to search here
        entry_query = get_query(query_string, ['itemName',])
        
        found_entries = LPReward.objects.filter(entry_query).order_by('itemName')
        
        # by default, sort sell by ascending price
        if ( request.GET.get('sort') ):
            order = request.GET.get('sort')
        else:
            order = 'itemName'
        
        results = LPResults(found_entries, order_by=order)

    return render_to_response('records/lp_search.html',
                              { 'query_string': query_string,
                               'results': results },
                              context_instance=RequestContext(request))

# LP Calculator:
# This should probably be done in AJAX or something.
#
# per item formula:
#
# profit[x] = ( sellPrice[x] - store_fee[x] - other_fee[x] ) / LP_cost[x]
#
# Where:
# -other_fee could be cost of purchasing T1 ammo to convert to faction)
# -sellPrice is determined by region & price stat (ex. mean, or high sell, etc)


# form to get item list for the LP calculator
class LPCalcItem(forms.Form):
    item = forms.MultipleChoiceField(choices=LPitems, widget=forms.SelectMultiple(attrs={'size': 30}))
    spendable = forms.IntegerField()

# to choose the region(s) and price statistic to use in calculations
class LPCalcDetails(forms.Form):
    __priceStats = (
        ('meanbp', 'Mean Buy Price'),
        #('medbp', 'Median Buy Price'),
        ('hbp', 'High Buy Price'),
        ('lbp', 'Low Buy Price'),
        ('meansp', 'Mean Sell Price'),
        #('medsp', 'Median Sell Price'),
        ('hsp', 'High Sell Price'),
        ('lsp', 'Low Sell Price')
    )
    region = forms.MultipleChoiceField(choices=regions)
    stat = forms.ChoiceField(choices=__priceStats)
    item_name = ''

class LPCalcResultsTable(tables.Table):
    itemName = tables.Column(verbose_name='Item')
    regionName = tables.Column(verbose_name='Region')
    sellPrice = tables.Column(verbose_name='Sell Price')
    storeFee = tables.Column(verbose_name='Store Fee')
    otherFee = tables.Column(verbose_name='Other Fee')
    lpCost = tables.Column(verbose_name='LP Cost')
    profitPer = tables.Column()
    profit = tables.Column()
    
    def render_sellPrice(self, value):
        return '%s' % locale.format('%.2f', value, grouping=True)
    
    def render_storeFee(self, value):
        return '%s' % locale.format('%.2f', value, grouping=True)
        
    def render_otherFee(self, value):
        return '%s' % locale.format('%.2f', value, grouping=True)
    
    def render_profitPer(self, value):
        return '%s' % locale.format('%.2f', value, grouping=True)
    
    def render_profit(self, value):
        return '%s' % locale.format('%.2f', value, grouping=True)
    
    class Meta:
        attrs = {'class': 'paleblue'}

# accepts iterables of typeID, regionID, __priceStats,
# calculates profits for each group of indices in params
# returns a dict to fill an LPCalcResultsTable
def calculate_profits(items, region, stat, spendable):
    count = len(items)
    data = list()
    for x in range(0, count):
        item = invTypes.objects.get(pk=items[x])
        item_name = item.typeName
        region_name = mapRegions.objects.get(regionID=region[x]).regionName
        profit_per = None
        profit = None
        
        # start limiting our query to typeID, regionID
        q = MarketRecord.objects.filter(typeID__exact=item).filter(stationID__regionID__exact=region[x])
        try:
            if stat[x] == 'meanbp':
                sell_price = q.filter(bid__exact=True).aggregate(tmp=Avg('price'))['tmp']
            elif stat[x] == 'hbp':
                sell_price = q.filter(bid__exact=True).aggregate(tmp=Max('price'))['tmp']
            elif stat[x] == 'lbp':
                sell_price = q.filter(bid__exact=True).aggregate(tmp=Min('price'))['tmp']
            elif stat[x] == 'meansp':
                sell_price = q.filter(bid__exact=False).aggregate(tmp=Avg('price'))['tmp']
            elif stat[x] == 'hsp':
                sell_price = q.filter(bid__exact=False).aggregate(tmp=Max('price'))['tmp']
            elif stat[x] == 'lsp':
                sell_price = q.filter(bid__exact=False).aggregate(tmp=Min('price'))['tmp']
            
            # We assume each LP-bought item will cost the same ISK, LP, and other_fee
            lp_reward = LPReward.objects.filter(itemName__exact=item_name)[0]
            store_fee = int(lp_reward.ISKcost)
            other_fee = int(0)
            lp_cost = int(lp_reward.LPcost)
            
            profit_per = (sell_price - store_fee - other_fee) / float(lp_cost)
            buyable = int(int(spendable) / lp_cost)
            profit = profit_per * buyable * lp_cost
            
            # profit_per = (isk/lp) for a each unit
            # total profit (isk) = profit_per (isk/lp) * buyable (n/a) * lp_cost (1/lp)
        
        except TypeError as e:
            print '!! Error in calculate_profits (sell_price assignment):', e
        
        if not profit_per:
            profit_per = 'ERROR'
        if not profit:
            profit = 'ERROR'
        
        data.append({'itemName': item_name, 'regionName': region_name,
                   'sellPrice': sell_price, 'storeFee': store_fee,
                   'otherFee': other_fee, 'lpCost': lp_cost,
                   'profitPer': profit_per, 'profit': profit})
        
    return data
    
# calculate profits from selling various LP store-bought items in any location
# given prevailing market conditions
def lp_calc(request):
    if request.method == 'GET':
        print '** lp_calc: GET:', request.GET

        form = LPCalcItem(request.GET)
        
        # 0: no 'step' param, so user must've just gotten here
        if 'step' not in request.GET:
            print '** On STEP 0...'
            # The starting point; an form w/o any input
        else:
            if request.GET.get('step') == '1':
                print '** On STEP 1...'
                
                # We now have an item list
                
                if form.is_valid():
                    print '** Form validated.'
                    
                    item_list = request.GET.getlist('item')
                    #print '** item_list:', item_list
                    
                    LPCalcDetailsFormSet = formset_factory(LPCalcDetails,
                                              extra=len(item_list))
                    
                    formset = LPCalcDetailsFormSet()
                    count = 0
                    
                    spendable = int(request.GET.get('spendable'))
                    
                    # Get the item name into each form, to use as a label on render
                    for form in formset:
                        form.item_name = invTypes.objects.get(pk=item_list[count]).typeName
                        count = count + 1
                    
                    return render_to_response('records/lp_calc2.html',
                                              {'formset': formset, 'items': item_list, 'spendable': spendable},
                                              context_instance=RequestContext(request))
            elif request.GET.get('step') == '2':
                print '** ON STEP 2...'
                #print '** GET:', request.GET
                
                # We now have an item list, as well as a region-priceStat combo for each item
                
                # Recreate the formset as it was made for this particular query
                LPCalcDetailsFormSet = formset_factory(LPCalcDetails,
                                          extra=request.GET.get('TOTAL_FORMS'))
                formset = LPCalcDetailsFormSet(request.GET)
                
                if formset.is_valid():
                    print '** Formset is valid:', formset.data
                    
                    items = request.GET.get('items')
                    item_count = len(items.split(';')) - 1 # -1 b/c of trailing semi-colon
                    item_list = items.split(';')[0:item_count]
                    
                    #print '** item_list:'
                    #for i in item_list:
                    #    print i
                    
                    #print '** formset len:', len(formset)
                    
                    form_count = int(request.GET.get('form-TOTAL_FORMS'))
                    
                    region = dict()
                    stat = dict()
                    for x in range(0, form_count):
                        region[x] = request.GET.get('form-' + str(x) + '-region')
                        stat[x] = request.GET.get('form-' + str(x) + '-stat')
                        
                    spendable = request.GET.get('spendable')
                    
                    table_data = calculate_profits(item_list, region, stat, spendable)
                    table = LPCalcResultsTable(table_data)
                    
                    print 'table_data:'
                    for k in range(0, len(table_data)):
                        print str(k) + ':', table_data[k]
                    
                    return render_to_response('records/lp_calc3.html',
                                              {'table': table},
                                              context_instance=RequestContext(request))
                    
    else:
        print '** NO GET.'
        form = LPCalcItem()
        
    return render_to_response('records/lp_calc.html', {'form': form},
                              context_instance=RequestContext(request))

# Type name lookup autocomplete view
def type_lookup(request):
    # Default return list
    results = []
    if request.method == "GET":
        if request.GET.has_key(u'query'):
            value = request.GET[u'query']
            # Ignore queries shorter than length 2
            if len(value) > 2:
                model_results = invTypes.objects.filter(typeName__icontains=value)
                results = [ x.typeName for x in model_results ]
    json = simplejson.dumps(results)
    return HttpResponse(json, mimetype='application/json')
    
# LP lookup autocomplete view
def lp_lookup(request):
    # Default return list
    results2 = []
    if request.method == "GET":
        if request.GET.has_key(u'query'):
            value = request.GET[u'query']
            # Ignore queries shorter than length 2
            if len(value) > 2:
                model_results2 = invTypes.objects.filter(isLPreward__exact=True).filter(typeName__icontains=value).order_by('typeName')
                results2 = [ x.typeName for x in model_results2 ]
    json = simplejson.dumps(results2)
    return HttpResponse(json, mimetype='application/json')
    
# view to handle the importing of LP Store data
def import_lp_data(request):
    print '** IN import_lp_data...'
    
    path = '/home/django/elc/eve_lp_store.csv'
    firstLine = True
    seen = set()
    
    if request.method == 'POST':        
        with open(path, 'rb') as f:
            reader = csv.reader(f)
            
            try:
                for row in reader:
                    
                    if firstLine == False:
                        toAdd = LPReward()
                        need = dict()
                        index = 1
                        reqItems = ''
                        
                        toAdd.corp = row[0]
                        toAdd.itemName = row[1]
                        toAdd.qty = row[2]
                        toAdd.LPcost = row[3]
                        toAdd.ISKcost = row[4]
                        
                        #print '** RAW row:', row
                        
                        # parse req'd items list
                        if (row[5] != '') & (row[5] != 'Reqired Items'):
                            splitd = re.split(' x ', row[5])
                            reqdCount = len(splitd) - 1
                            #print '** splitd:', splitd
                            
                            # get first requirement; key = item name, val = qty
                            if index == 1:
                                need[splitd[index][0:splitd[index].rfind(' ')]] = splitd[index-1]
                            
                            # loop through each of the remaining elements
                            while index < len(splitd) - 1:
                                index = index + 1
                                if ( index == len(splitd) - 1): # non-first/last items will have item name followed by qty of NEXT item
                                    need[splitd[index]] = int(splitd[index-1][splitd[index-1].rfind(' '):len(splitd[index-1])])
                                else:   # last item will be just the item name
                                    need[splitd[index][0:splitd[index].rfind(' ')]] = int(splitd[index-1][splitd[index-1].rfind(' '):len(splitd[index-1])])
                                    
                            # store req'd items' typeID followed by comma, followed by qty of typeID, followed by comma
                            for key in need:
                                reqItems = reqItems + str(invTypes.objects.get(typeName = key).typeID) + ','
                                reqItems = reqItems + str(need[key]) + ','
                            
                            reqItems = reqItems[0:len(reqItems)-1]    
                            toAdd.requiredItems = reqItems
                                                    
                            #print '** reqItems:', reqItems
                        else:
                            #print '** No required items found.'
                            reqItems = ''
                        
                        #print '** toAdd: corp:%s, itemName:%s, qty:%s, LPcost:%s, ISKcost:%s, requiredItems:%s' % (toAdd.corp, toAdd.itemName, toAdd.qty, toAdd.LPcost, toAdd.ISKcost, toAdd.requiredItems)
                        toAdd.save()
                        
                        if toAdd.itemName not in seen:
                            seen.add(toAdd.itemName)
                            
                            try:
                                x = invTypes.objects.get(typeName = toAdd.itemName)
                                x.isLPreward = True
                                x.save()
                            except Exception as detail:
                                print '!! ERROR in import_lp_data (typeName: "' + toAdd.itemName + '"):', detail
                                continue
                    
                    firstLine = False
                    
            except csv.Error, e:
                print '!! import_lp_data: CSV error in file %s, line %d: %s' % (path, reader.line_num, e)
                
            f.close()
    
    return render_to_response('records/import_lp.html',
                              context_instance=RequestContext(request))

def lp_detail(request, type_id):
    try:
        item = LPReward.objects.get(pk=type_id)
    except invTypes.DoesNotExist:
        raise Http404   # perhaps display a more informative page
    
    # dict to hold the attributes of the item in question
    attrs = {}
    
    # fill dict with attribute names as keys, and the int/float as values
    for x in dgmTypeAttributes.objects.filter(typeID=item.typeID):
        if x.valueInt:
            attrs[x.attributeID.attributeName] = x.valueInt
        else:
            attrs[x.attributeID.attributeName] = x.valueFloat
        
    #print '** attrs:', attrs.items()
        
    buy = None
    sell = None
    
    # by default, sort buy orders by descending price
    if ( request.GET.get('b-sort') ):
        bOrder = request.GET.get('b-sort')
    else:
        bOrder = '-price'
    
    # by default, sort sell by ascending price
    if ( request.GET.get('s-sort') ):
        sOrder = request.GET.get('s-sort')
    else:
        sOrder = 'price'
        
    buy = DetailTable(item.marketrecord_set.filter(bid__exact=1),
                        prefix='b-', order_by=bOrder)
    
    sell = DetailTable(item.marketrecord_set.filter(bid__exact=0),
                        prefix='s-', order_by=sOrder)
    
    return render_to_response('records/type_detail.html',
                              { 'buy': buy, 'sell': sell, 'item': item,
                               'attrs': attrs },
                              context_instance=RequestContext(request))