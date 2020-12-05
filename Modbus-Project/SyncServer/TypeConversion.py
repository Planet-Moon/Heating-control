from math import floor

def list_to_number(number, length=2, signed=False): #little endian
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
            signed_Number = unsigned_number - ~mask
        else:
            signed_Number = unsigned_number & ~mask
        return signed_Number

def number_to_wordList(number, signed=False):
    numberInternal = number
    needBytes = 0
    testValue = 0
    returnList = []
    while testValue < number:
        needBytes += 1
        testValue = 2**(16*needBytes)
        returnList.append(round(numberInternal % (2**16)))
        numberInternal = numberInternal / (2**16)
        pass
    returnList = list(reversed(returnList))
    return returnList

def main():
    testList = [100, 1, 0, 92]
    print("testList:"+str(testList))
    testNumber = list_to_number(testList)
    print("testNumber:"+str(testNumber))
    testList = number_to_wordList(testNumber)
    print("testList:"+str(testList))


if __name__ == "__main__":
    main()