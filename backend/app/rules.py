# Deliberately illustrative configuration. No official APH mapping is asserted.
RULES={
 'new_institution':{'label':'Establishment of a new technical institution','track':'T1 · Heavy physical and legal verification','route':['scrutiny','evc','decision'],'slots':['Building plan','Land title or lease deed','Occupancy or completion certificate','Fire safety certificate','Financial status certificate','Institution affidavit','Organisation resolution','Detailed project report'],'days':7},
 'eoa':{'label':'Extension of Approval (EoA) based on self-disclosure','track':'T3 · Routine and fast-track approvals','route':['scrutiny','decision'],'slots':['Institution affidavit','Prior approval','Occupancy or completion certificate','Satellite map','Audited statement of accounts'],'days':7},
 'nri_seats':{'label':'Introduction or continuation of NRI seats','track':'T3 · Routine and fast-track approvals','route':['scrutiny','decision'],'slots':['Organisation resolution','NRI seat declaration','Approved intake statement'],'days':7},
 'fn_oci_seats':{'label':'Supernumerary seats for FN, OCI, or Gulf workers','track':'T3 · Routine and fast-track approvals','route':['scrutiny','decision'],'slots':['International office and hostel details','Enrollment or Study in India evidence','Supernumerary seat declaration'],'days':7},
 'new_course':{'label':'Increase in intake or additional course','track':'T2 · Academic and programme modifications','route':['scrutiny','evc','decision'],'slots':['Affidavit 8','Organisation resolution','Faculty and infrastructure statement'],'days':7},
 'level_conversion':{'label':'Conversion of diploma level into degree level and vice versa','track':'T2 · Academic and programme modifications','route':['scrutiny','decision'],'slots':['University or board NOC','Organisation resolution','Five-year operating history'],'days':7},
 'new_programme':{'label':'Start a new programme or level','track':'T2 · Academic and programme modifications','route':['scrutiny','decision'],'slots':['University or board NOC','Organisation resolution','Campus resource statement'],'days':7},
 'integrated_degree':{'label':'Introduction of an integrated or dual degree course','track':'T2 · Academic and programme modifications','route':['scrutiny','decision'],'slots':['Affidavit 8','Organisation resolution','University or board NOC','Baseline programme evidence'],'days':7},
 'fpm':{'label':'Introduction or continuation of Fellow Programme in Management','track':'T2 · Academic and programme modifications','route':['scrutiny','decision'],'slots':['Qualified faculty evidence','Research publication evidence','FPM programme declaration'],'days':7},
 'twinning':{'label':'Collaboration and twinning programme','track':'T2 · Academic and programme modifications','route':['scrutiny','decision'],'slots':['Bipartite MoU','Authorised collaboration letter','University or board NOC','Affidavit 11'],'days':7},
 'break_restoration':{'label':'EoA after break, restoration, or hibernation','track':'T2 · Academic and programme modifications','route':['scrutiny','evc','decision'],'slots':['Past deficiency compliance report','Financial viability proof','Break-period declaration'],'days':7},
 'gender_conversion':{'label':'Conversion between women’s and co-educational institution','track':'T2 · Academic and programme modifications','route':['scrutiny','decision'],'slots':['University or board NOC','Organisation resolution','Safety and amenities statement'],'days':7},
 'merger':{'label':'Merger of institutions under the same or different promoter','track':'T4 · Structural and administrative reorganisation','route':['scrutiny','decision'],'slots':['University or board NOC','Organisation resolutions','Land transfer deeds','Combined infrastructure statement'],'days':7},
 'closure_institution':{'label':'Closure of the institution','track':'T4 · Structural and administrative reorganisation','route':['scrutiny','decision'],'slots':['University or board NOC','Latest salary sheet','Closure affidavit','Student reallocation plan'],'days':7},
 'closure_programme':{'label':'Closure of programmes or reduction in intake','track':'T4 · Structural and administrative reorganisation','route':['scrutiny','decision'],'slots':['University or board NOC','Organisation resolution','Student and intake impact statement'],'days':7},
 'name_affiliation_change':{'label':'Change in institution name or affiliating university/board','track':'T4 · Structural and administrative reorganisation','route':['scrutiny','decision'],'slots':['University or board NOC','Organisation resolution','Name compliance declaration'],'days':7},
 'promoter_change':{'label':'Change in name or address of trust, society, or company','track':'T4 · Structural and administrative reorganisation','route':['scrutiny','decision'],'slots':['Registrar or ROC approval','Notarised affidavit 10','Registered trust deed','Land transfer proof'],'days':7},
 'bank_change':{'label':'Change in bank details','track':'T4 · Structural and administrative reorganisation','route':['scrutiny','decision'],'slots':['Notarised affidavit 9','Organisation resolution','TER fee payment receipt'],'days':7},
 'university_conversion':{'label':'Conversion into a deemed-to-be university or university','track':'T4 · Structural and administrative reorganisation','route':['scrutiny','decision'],'slots':['Government Gazette or UGC declaration','University NOC','Affidavits 2 and 5','Technical programme transition plan'],'days':7},
 'online_odl':{'label':'Online learning or open and distance learning courses','track':'T2 · Academic and programme modifications','route':['scrutiny','decision'],'slots':['Accreditation or ranking certificate','Distance education infrastructure proof','LMS details','Affidavits 2 and 5'],'days':7},
}
VERSION='DEMO-2026-v1'
SOURCE='Illustrative prototype rules · NEEDS_APH_VERIFICATION'

def validate_definitions(definitions):
    if not isinstance(definitions,dict) or not definitions:
        raise ValueError('Rule definitions must be a non-empty object')
    for kind,definition in definitions.items():
        if not isinstance(kind,str) or not isinstance(definition,dict):
            raise ValueError('Each rule must be an object keyed by application type')
        route=definition.get('route')
        slots=definition.get('slots')
        if not isinstance(route,list) or len(route)<2 or any(not isinstance(x,str) or not x for x in route):
            raise ValueError(f'{kind}: route must contain at least two named stages')
        if not isinstance(slots,list) or not slots or any(not isinstance(x,str) or not x for x in slots):
            raise ValueError(f'{kind}: slots must contain named evidence requirements')
        if len(set(route))!=len(route):
            raise ValueError(f'{kind}: route stages must be unique')
        if not isinstance(definition.get('label'),str) or not definition['label'].strip():
            raise ValueError(f'{kind}: label is required')
        if not isinstance(definition.get('days'),int) or definition['days']<=0:
            raise ValueError(f'{kind}: days must be a positive integer')
