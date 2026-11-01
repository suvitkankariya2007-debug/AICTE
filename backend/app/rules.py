# Deliberately illustrative configuration. No official APH mapping is asserted.
RULES={
 'new_institution':{'label':'New institution','route':['scrutiny','evc','decision'],'slots':['Institution declaration','Land evidence','Building evidence'],'days':7},
 'new_course':{'label':'New course / intake increase','route':['scrutiny','evc','decision'],'slots':['Institution declaration','Programme proposal','Faculty statement'],'days':7},
 'eoa':{'label':'Extension of approval','route':['scrutiny','decision'],'slots':['Institution declaration','Prior approval','Compliance declaration'],'days':7},
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
