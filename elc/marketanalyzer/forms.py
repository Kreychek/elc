from django import forms

from marketanalyzer.models import LPitems

regions = [(10000001, u'Derelik (10000001)'), (10000002, u'The Forge (10000002)'), (10000003, u'Vale of the Silent (10000003)'), (10000004, u'UUA-F4 (10000004)'), (10000005, u'Detorid (10000005)'), (10000006, u'Wicked Creek (10000006)'), (10000007, u'Cache (10000007)'), (10000008, u'Scalding Pass (10000008)'), (10000009, u'Insmother (10000009)'), (10000010, u'Tribute (10000010)'), (10000011, u'Great Wildlands (10000011)'), (10000012, u'Curse (10000012)'), (10000013, u'Malpais (10000013)'), (10000014, u'Catch (10000014)'), (10000015, u'Venal (10000015)'), (10000016, u'Lonetrek (10000016)'), (10000017, u'J7HZ-F (10000017)'), (10000018, u'The Spire (10000018)'), (10000019, u'A821-A (10000019)'), (10000020, u'Tash-Murkon (10000020)'), (10000021, u'Outer Passage (10000021)'), (10000022, u'Stain (10000022)'), (10000023, u'Pure Blind (10000023)'), (10000025, u'Immensea (10000025)'), (10000027, u'Etherium Reach (10000027)'), (10000028, u'Molden Heath (10000028)'), (10000029, u'Geminate (10000029)'), (10000030, u'Heimatar (10000030)'), (10000031, u'Impass (10000031)'), (10000032, u'Sinq Laison (10000032)'), (10000033, u'The Citadel (10000033)'), (10000034, u'The Kalevala Expanse (10000034)'), (10000035, u'Deklein (10000035)'), (10000036, u'Devoid (10000036)'), (10000037, u'Everyshore (10000037)'), (10000038, u'The Bleak Lands (10000038)'), (10000039, u'Esoteria (10000039)'), (10000040, u'Oasa (10000040)'), (10000041, u'Syndicate (10000041)'), (10000042, u'Metropolis (10000042)'), (10000043, u'Domain (10000043)'), (10000044, u'Solitude (10000044)'), (10000045, u'Tenal (10000045)'), (10000046, u'Fade (10000046)'), (10000047, u'Providence (10000047)'), (10000048, u'Placid (10000048)'), (10000049, u'Khanid (10000049)'), (10000050, u'Querious (10000050)'), (10000051, u'Cloud Ring (10000051)'), (10000052, u'Kador (10000052)'), (10000053, u'Cobalt Edge (10000053)'), (10000054, u'Aridia (10000054)'), (10000055, u'Branch (10000055)'), (10000056, u'Feythabolis (10000056)'), (10000057, u'Outer Ring (10000057)'), (10000058, u'Fountain (10000058)'), (10000059, u'Paragon Soul (10000059)'), (10000060, u'Delve (10000060)'), (10000061, u'Tenerifis (10000061)'), (10000062, u'Omist (10000062)'), (10000063, u'Period Basis (10000063)'), (10000064, u'Essence (10000064)'), (10000065, u'Kor-Azor (10000065)'), (10000066, u'Perrigen Falls (10000066)'), (10000067, u'Genesis (10000067)'), (10000068, u'Verge Vendor (10000068)'), (10000069, u'Black Rise (10000069)'), (11000001, u'Unknown (11000001)'), (11000002, u'Unknown (11000002)'), (11000003, u'Unknown (11000003)'), (11000004, u'Unknown (11000004)'), (11000005, u'Unknown (11000005)'), (11000006, u'Unknown (11000006)'), (11000007, u'Unknown (11000007)'), (11000008, u'Unknown (11000008)'), (11000009, u'Unknown (11000009)'), (11000010, u'Unknown (11000010)'), (11000011, u'Unknown (11000011)'), (11000012, u'Unknown (11000012)'), (11000013, u'Unknown (11000013)'), (11000014, u'Unknown (11000014)'), (11000015, u'Unknown (11000015)'), (11000016, u'Unknown (11000016)'), (11000017, u'Unknown (11000017)'), (11000018, u'Unknown (11000018)'), (11000019, u'Unknown (11000019)'), (11000020, u'Unknown (11000020)'), (11000021, u'Unknown (11000021)'), (11000022, u'Unknown (11000022)'), (11000023, u'Unknown (11000023)'), (11000024, u'Unknown (11000024)'), (11000025, u'Unknown (11000025)'), (11000026, u'Unknown (11000026)'), (11000027, u'Unknown (11000027)'), (11000028, u'Unknown (11000028)'), (11000029, u'Unknown (11000029)'), (11000030, u'Unknown (11000030)')]
lp_corps = [(u'All', u'All'), (u'24th Imperial Crusade', u'24th Imperial Crusade'), (u'Aliastra', u'Aliastra'), (u'Allotek Industries', u'Allotek Industries'), (u'Amarr Certified News', u'Amarr Certified News'), (u'Amarr Civil Service', u'Amarr Civil Service'), (u'Amarr Constructions', u'Amarr Constructions'), (u'Amarr Navy', u'Amarr Navy'), (u'Amarr Trade Registry', u'Amarr Trade Registry'), (u'Ammatar Consulate', u'Ammatar Consulate'), (u'Ammatar Fleet', u'Ammatar Fleet'), (u'Archangels', u'Archangels'), (u'Ardishapur Family', u'Ardishapur Family'), (u'Astral Mining Inc.', u'Astral Mining Inc.'), (u'Bank of Luminaire', u'Bank of Luminaire'), (u'Blood Raiders', u'Blood Raiders'), (u'Boundless Creation', u'Boundless Creation'), (u'Brutor tribe', u'Brutor tribe'), (u'Caldari Business Tribunal', u'Caldari Business Tribunal'), (u'Caldari Constructions', u'Caldari Constructions'), (u'Caldari Funds Unlimited', u'Caldari Funds Unlimited'), (u'Caldari Navy', u'Caldari Navy'), (u'Caldari Provisions', u'Caldari Provisions'), (u'Caldari Steel', u'Caldari Steel'), (u'Carthum Conglomerate', u'Carthum Conglomerate'), (u'CBD Corporation', u'CBD Corporation'), (u'CBD Sell Division', u'CBD Sell Division'), (u'Center for Advanced Studies', u'Center for Advanced Studies'), (u'Chemal Tech', u'Chemal Tech'), (u'Chief Executive Panel', u'Chief Executive Panel'), (u'Civic Court', u'Civic Court'), (u'Combined Harvest', u'Combined Harvest'), (u'CONCORD', u'CONCORD'), (u'Core Complexion Inc.', u'Core Complexion Inc.'), (u'Corporate Police Force', u'Corporate Police Force'), (u'Court Chamberlain', u'Court Chamberlain'), (u'CreoDron', u'CreoDron'), (u'Deep Core Mining Inc.', u'Deep Core Mining Inc.'), (u'Dominations', u'Dominations'), (u'Ducia Foundry', u'Ducia Foundry'), (u'Duvolle Laboratories', u'Duvolle Laboratories'), (u'Echelon Entertainment', u'Echelon Entertainment'), (u'Egonics Inc.', u'Egonics Inc.'), (u'Eifyr and Co.', u'Eifyr and Co.'), (u'Emperor Family', u'Emperor Family'), (u'Expert Distribution', u'Expert Distribution'), (u'Expert Housing', u'Expert Housing'), (u'Federal Administration', u'Federal Administration'), (u'Federal Defence Union', u'Federal Defence Union'), (u'Federal Freight', u'Federal Freight'), (u'Federal Intelligence Office', u'Federal Intelligence Office'), (u'Federal Navy Academy', u'Federal Navy Academy'), (u'Federation Customs', u'Federation Customs'), (u'Federation Navy', u'Federation Navy'), (u'FedMart', u'FedMart'), (u'Food Relief', u'Food Relief'), (u'Freedom Extension', u'Freedom Extension'), (u'Further Foodstuffs', u'Further Foodstuffs'), (u'Garoun Investment Bank', u'Garoun Investment Bank'), (u'Guardian Angels', u'Guardian Angels'), (u'Guristas', u'Guristas'), (u'Guristas Production', u'Guristas Production'), (u'Hedion University', u'Hedion University'), (u'Home Guard', u'Home Guard'), (u'House of Records', u'House of Records'), (u'Hyasyoda Corporation', u'Hyasyoda Corporation'), (u'HZO Refinery', u'HZO Refinery'), (u'Imperial Academy', u'Imperial Academy'), (u'Imperial Armaments', u'Imperial Armaments'), (u'Imperial Chancellor', u'Imperial Chancellor'), (u'Imperial Shipment', u'Imperial Shipment'), (u'Impetus', u'Impetus'), (u'Inherent Implants', u'Inherent Implants'), (u'Inner Zone Shipping', u'Inner Zone Shipping'), (u'Intaki Bank', u'Intaki Bank'), (u'Intaki Commerce', u'Intaki Commerce'), (u'Intaki Space Police', u'Intaki Space Police'), (u'Intaki Syndicate', u'Intaki Syndicate'), (u'Internal Security', u'Internal Security'), (u'Ishukone Corporation', u'Ishukone Corporation'), (u'Ishukone Watch', u'Ishukone Watch'), (u'Joint Harvesting', u'Joint Harvesting'), (u'Kaalakiota Corporation', u'Kaalakiota Corporation'), (u'Kador Family', u'Kador Family'), (u'Khanid Innovation', u'Khanid Innovation'), (u'Khanid Transport', u'Khanid Transport'), (u'Khanid Works', u'Khanid Works'), (u'Kor Azor Family', u'Kor Azor Family'), (u'Krusual tribe', u'Krusual tribe'), (u'Lai Dai Corporation', u'Lai Dai Corporation'), (u'Lai Dai Protection Service', u'Lai Dai Protection Service'), (u'Material Acquisition', u'Material Acquisition'), (u'Mercantile Club', u'Mercantile Club'), (u'Minedrill', u'Minedrill'), (u'Ministry of Assessment', u'Ministry of Assessment'), (u'Ministry of Internal Order', u'Ministry of Internal Order'), (u'Ministry of War', u'Ministry of War'), (u'Minmatar Mining Corporation', u'Minmatar Mining Corporation'), (u'Modern Finances', u'Modern Finances'), (u'Mordus Legion', u'Mordus Legion'), (u'Native Freshfood', u'Native Freshfood'), (u'Nefantar Miner Association', u'Nefantar Miner Association'), (u'Noble Appliances', u'Noble Appliances'), (u'Nugoeihuvi Corporation', u'Nugoeihuvi Corporation'), (u'Nurtura', u'Nurtura'), (u'Outer Ring Excavations', u'Outer Ring Excavations'), (u'Pator Tech School', u'Pator Tech School'), (u'Peace and Order Unit', u'Peace and Order Unit'), (u'Pend Insurance', u'Pend Insurance'), (u'Perkone', u'Perkone'), (u'Poksu Mineral Group', u'Poksu Mineral Group'), (u'Poteque Pharmaceuticals', u'Poteque Pharmaceuticals'), (u'President', u'President'), (u'Prompt Delivery', u'Prompt Delivery'), (u'Propel Dynamics', u'Propel Dynamics'), (u'Quafe Company', u'Quafe Company'), (u'Rapid Assembly', u'Rapid Assembly'), (u'Republic Fleet', u'Republic Fleet'), (u'Republic Justice Department', u'Republic Justice Department'), (u'Republic Military School', u'Republic Military School'), (u'Republic Parliament', u'Republic Parliament'), (u'Republic Security Services', u'Republic Security Services'), (u'Republic University', u'Republic University'), (u'Roden Shipyards', u'Roden Shipyards'), (u'Royal Amarr Institute', u'Royal Amarr Institute'), (u'Royal Khanid Navy', u'Royal Khanid Navy'), (u'Salvation Angels', u'Salvation Angels'), (u'Sarum Family', u'Sarum Family'), (u'School of Applied Knowledge', u'School of Applied Knowledge'), (u'Science and Trade Institute', u'Science and Trade Institute'), (u'Sebiestor tribe', u'Sebiestor tribe'), (u'Senate', u'Senate'), (u'Serpentis Corporation', u'Serpentis Corporation'), (u'Serpentis Inquest', u'Serpentis Inquest'), (u'Sisters of EVE', u'Sisters of EVE'), (u'Six Kin Development', u'Six Kin Development'), (u'Spacelane Patrol', u'Spacelane Patrol'), (u'State and Region Bank', u'State and Region Bank'), (u'State Protectorate', u'State Protectorate'), (u'State War Academy', u'State War Academy'), (u'Sukuuvestaa Corporation', u'Sukuuvestaa Corporation'), (u'Supreme Court', u'Supreme Court'), (u'Tash Murkon Family', u'Tash Murkon Family'), (u'The Leisure Group', u'The Leisure Group'), (u'Theology Council', u'Theology Council'), (u'The Sanctuary', u'The Sanctuary'), (u'The Scope', u'The Scope'), (u'Thukker Mix', u'Thukker Mix'), (u'Top Down', u'Top Down'), (u'TransStellar Shipping', u'TransStellar Shipping'), (u'Tribal Liberation Force', u'Tribal Liberation Force'), (u'True Creations', u'True Creations'), (u'True Power', u'True Power'), (u'Trust Partners', u'Trust Partners'), (u'University of Caille', u'University of Caille'), (u'Urban Management', u'Urban Management'), (u'Vherokior tribe', u'Vherokior tribe'), (u'Viziam', u'Viziam'), (u'Wiyrkomi Corporation', u'Wiyrkomi Corporation'), (u'Wiyrkomi Peace Corps', u'Wiyrkomi Peace Corps'), (u'Ytiri', u'Ytiri'), (u'Zainou', u'Zainou'), (u'Zero G Research Firm', u'Zero G Research Firm'), (u'Zoar and Sons', u'Zoar and Sons')]
theme_choices = [('dark', 'Dark'), ('blue', 'Blue')]

# Form used for uploading market dumps.
class UploadFileForm(forms.Form):
    file  = forms.FileField()

# Form to get list of item(s) for the LP calculator.
class LPCalcItem(forms.Form):
    # 'size' attr is height of widget (# of entries visible)
    item = forms.MultipleChoiceField(choices=LPitems,
                                     widget=forms.SelectMultiple(
                                        attrs={'size': 30}))
    spendable = forms.IntegerField() # the amt of LP available to spend
    
    error_css_class = 'error'
    required_css_class = 'required'

# Form to choose the region and price statistic for each item to use in
# calculations.
class LPCalcDetails(forms.Form):
    # Available price stat options. These are all generated by SQL aggregate
    # functions performed on a filtered query.
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

# Form to allow filtering on the LP reward search.
class LPSearchFilter(forms.Form):
    typeid = forms.CharField(label='Search for a type of item by name (ex. "eifyr", "sansha tag", "xl")',
                             min_length=3,
                             widget=forms.TextInput(attrs={'size': '50'}))
    corp = forms.ChoiceField(choices=lp_corps, label='Corporation')

class ThemeSelector(forms.Form):
    themes = forms.ChoiceField(choices=theme_choices, label='Theme')
    from_url = forms.HiddenInput()