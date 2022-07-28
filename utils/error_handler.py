from discord.ext.commands import CheckFailure


class ErrorMemberNotAdministrator(CheckFailure):
    def __init__(self):
        super().__init__(message="Le membre n'est pas un administrateur")


class ErrorMemberLowerRank(CheckFailure):
    def __init__(self):
        super().__init__(message="Le membre ne peux pas effectuer d'action sur cet utilisateur")


class ErrorMemberNotBotOwner(CheckFailure):
    def __init__(self):
        super().__init__(message="Le membre n'est pas un le développeur du bot")


class ErrorMemberNotModerator(CheckFailure):
    def __init__(self):
        super().__init__(message="Le membre n'est pas un modérateur")


class ErrorGuildNotWhitelisted(CheckFailure):
    def __init__(self):
        super().__init__(message="Le bot est disponible uniquement dans les serveurs whitelistés")


class ErrorPaginatorCharacter(CheckFailure):
    def __init__(self):
        super().__init__(message="Le message dépasse la limite autorisé par discord (2000 caractères)")


class ErrorUnknownRule(CheckFailure):
    def __init__(self):
        super().__init__(message="La règle spécifié n'existe pas")


class ErrorUnknownLogType(CheckFailure):
    def __init__(self):
        super().__init__(message="Le type de log spécifié n'existe pas")


class ErrorTooMuchArguments(CheckFailure):
    def __init__(self):
        super().__init__(message="La commande possède trop d'arguments")


class ErrorUnknownAliase(CheckFailure):
    def __init__(self):
        super().__init__(message="Cet argument n'existe pas")


class ErrorAlreadyExist(CheckFailure):
    def __init__(self):
        super().__init__(message="Cet argument existe deja")


class ErrorDontExist(CheckFailure):
    def __init__(self):
        super().__init__(message="Cet argument n'existe pas")


class ErrorIncorrectForm(CheckFailure):
    def __init__(self):
        super().__init__(message="Cet argument a mal été spécifié")


class ErrorMissingArgument(CheckFailure):
    def __init__(self):
        super().__init__(message="Cet argument a mal été rempli")
