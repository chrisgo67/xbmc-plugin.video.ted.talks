def create_context_menu(getLS):
    context_menu = []
    context_menu += [(getLS(30097), 'Action(queue)')]
    context_menu += [(getLS(30098), 'Action(ToggleWatched)')]
    return context_menu
