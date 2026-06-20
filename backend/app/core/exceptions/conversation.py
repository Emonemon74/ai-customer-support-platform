class ConversationNotFoundError(Exception):
    def __init__(self):
        self.message = "Conversation not found"
        super().__init__(self.message)


class ConversationAccessDeniedError(Exception):
    def __init__(self):
        self.message = "You are not authorized to access this conversation"
        super().__init__(self.message)


class ConversationDeleteDeniedError(Exception):
    def __init__(self):
        self.message = "You are not authorized to delete this conversation"
        super().__init__(self.message)


class ConversationRenameDeniedError(Exception):
    def __init__(self):
        self.message = "You are not authorized to rename this conversation"
        super().__init__(self.message)