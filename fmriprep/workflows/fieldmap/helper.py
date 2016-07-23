from fmriprep.utils import misc
import re

def sort_fmaps(fieldmaps): # i.e. filenames
    from fmriprep.utils import misc
    from fmriprep.workflows.fieldmap.helper import is_fmap_type

    fmaps = {}
    for fmap_type in misc.fieldmap_suffixes.keys():
        fmaps[fmap_type] = []
        fmaps[fmap_type] = [doc for doc in fieldmaps
                            if is_fmap_type(fmap_type, doc)]
    # funky return statement so sort_fmaps can be a Function interface
    return [fmaps[key] for key in sorted(misc.fieldmap_suffixes.keys())]
        
def is_fmap_type(fmap_type, filename):
    return re.search(misc.fieldmap_suffixes[fmap_type], filename)