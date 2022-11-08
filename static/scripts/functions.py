def trim(string_to_trim):
    trimmed_string = ""
    for word in string_to_trim.split(" "):
        if word:
            trimmed_string += word + " "
    return trimmed_string


def has_only_allowed_symbols(*args, allowed_symbols="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_@.-+"):
    for arg in args:
        for letter in arg:
            if not letter in allowed_symbols:
                return False
    return True


def empty(*args):
    for arg in args:
        if trim(arg) == "":
            return True
    return False



def skip_by_one_char(first, second, n):
    imbalance = 0
    a = 0
    b = 0
    i = 0
    while (i < n and imbalance <= 1):
        if (first[a] == second[b]):
            #  When both string character at position a and b is same
            a += 1
            b += 1
        else:
            a += 1
            imbalance += 1

        i += 1

    if (imbalance == 0):
        #  In case, last character is extra in first string
        return 1

    return imbalance
    

def differ_by_single_char(first, second):
    #  Get the size of given string
    n = len(first)
    m = len(second)
    imbalance = 0
    if (n == m):
        i = 0
        #  Case A when both string are equal size
        while (i < n and imbalance <= 1):
            if (first[i] != second[i]):
                imbalance += 1

            i += 1

    elif (n - m == 1 or m - n == 1):
        #  When one string contains extra character
        if (n > m):
            imbalance = skip_by_one_char(first, second, m)
        else:
            imbalance = skip_by_one_char(second, first, n)

    return imbalance == 1


def is_valid_email(email):
    if not "@" in email or not "." in email:
        return False
    if email.count("@") > 1:
        return False
    if email.index("@") > email.index("."):
        return False
    return True