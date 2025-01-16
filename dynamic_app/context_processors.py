from .models import Folder

def folder_hierarchy(request):
    """
    A context processor to provide folder hierarchy to all templates.
    """
    folders = Folder.objects.filter(parent=None)  # Fetch top-level folders
    return {'folders': folders}