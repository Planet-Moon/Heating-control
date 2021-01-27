from math import floor

def list_to_number(number, length=2, signed=False): #little endian
    """Convert list of integers to a single integer

    Args:
        number (list): List to be converted
        length (int, optional): Wordlength of the list. Defaults to 2.
        signed (bool, optional): True if data should be signed. Defaults to False.

    Returns:
        int: Converted list to a single integer
    """
    unsigned_number = 0
    number_length = len(number)-1
    for i in range(number_length, -1, -1):
        factor = pow(2,16*(number_length-i))
        unsigned_number += number[i] * factor
        pass
    if not signed:
        return unsigned_number
    else:
        mask = 1 << 15 + number_length * 16
        if unsigned_number & mask:
            # negative
            signed_Number = (unsigned_number & ~mask) - mask
        else:
            # positive
            signed_Number = unsigned_number & ~mask
        return signed_Number

def number_to_wordList(number, signed=False, size=1):
    """Convert list to a wordlist. Splits a integer into multiple 16-bit integers.

    Args:
        number (int): Large integer to be converted
        signed (bool, optional): True if data should be signed. Defaults to False.
        size (int, optional): Length of the output list. Defaults to 1.

    Returns:
        list: List of 16-bit integers representing the input number
    """
    numberInternal = number
    needBytes = 0
    testValue = 0
    returnList = [0] * size
    while testValue < number:
        needBytes += 1
        testValue = 2**(16*needBytes)
        appendValue = round(numberInternal % (2**16))
        returnList[needBytes-1] = appendValue
        numberInternal = int(numberInternal / (2**16))
        pass
    returnList = list(reversed(returnList))
    return returnList

def main():
    testList = [32768, 240]
    print("testList:"+str(testList))
    testNumber = list_to_number(testList, signed=True)
    print("testNumber:"+str(testNumber))
    testList = number_to_wordList(testNumber, signed=True, size=len(testList))
    print("testList:"+str(testList))


if __name__ == "__main__":
    main()