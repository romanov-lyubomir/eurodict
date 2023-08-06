def trim(string_to_trim):
    trimmed_string = ""
    for word in string_to_trim.split(" "):
        if word:
            trimmed_string += word + " "
    return trimmed_string


def has_only_allowed_symbols(*args, allowed_symbols="_0123456789"):
    for arg in args:
        for letter in arg:
            if (
                not "a" <= letter <= "z"
                and not "A" <= letter <= "Z"
                and not letter in allowed_symbols
            ):
                return False
    return True


def empty(*args):
    for arg in args:
        if trim(arg) == "":
            return True
    return False


def differ_by_single_char(s1, s2):
    def remove_char_at_index(s, i):
        return s[:i] + s[i + 1 :]

    def swap_char_at_index(s, i):
        return s[:i] + s[i + 1] + s[i] + s[i + 2 :]

    if s1 == s2:
        return False
    if len(s1) < len(s2):
        s1, s2 = s2, s1
    if len(s1) - len(s2) > 1:
        return False
    elif s1[: len(s2)] == s2:
        return True
    diff = 0
    for i in range(len(s2)):
        if s1[i] != s2[i]:
            diff += 1
    if diff == 1:
        return True
    for i in range(len(s1)):
        if remove_char_at_index(s1, i) == s2:
            return True
    for i in range(len(s1) - 1):
        if swap_char_at_index(s1, i) == s2:
            return True
    return False


def is_valid_email(email):
    if email[0] == "." or email[-1] == ".":
        return False
    if email[0] == "@" or email[-1] == "@":
        return False
    if email.count("@") != 1:
        return False
    if not "." in email:
        return False
    # Check if the email has two dots next to each other
    for i in range(len(email) - 1):
        if email[i] == "." and email[i + 1] == ".":
            return False
    if not has_only_allowed_symbols(
        email, allowed_symbols="._-@0123456789abcdefghijklmnopqrstuvwxyz"
    ):
        return False
    return True
