def trisign_of(value):
    return compare(0, value)
        
def compare(a, b):
    if a < b:
        return 1
    elif a > b:
        return -1
    else:
        assert a == b
        return 0



def trisign_weakly_describes_order(trisign_to_compare, pair):
    a, b = pair
    """
    if a == b:
        return True
    if sign_to_compare == 1:
        return a < b
    elif sign_to_compare == -1:
        return a > b
    elif sign_to_compare == 0:
        return a
    """
    assert trisign_to_compare in {-1, 0, 1}
    comparison = compare(a, b)
    if comparison == 0:
        return True
    elif trisign_to_compare == 0:
        # comparison != 0, so trisign of 0 can't describe it even weakly.
        return False
    return trisign_to_compare == comparison
    
assert all(trisign_weakly_describes_order(*testVals) for testVals in [(1,(5,6)),(1,(5,5)),(0,(5,5)),(-1,(5,5)),(-1,(5,4))])
assert all((not trisign_weakly_describes_order(*testVals)) for testVals in [(0,(5,6)),(-1,(5,6)),(1,(5,4)),(0,(5,4))])


def number_trisign_weakly_describes_order(number_to_compare, pair):
    return trisign_weakly_describes_order(trisign_of(number_to_compare), pair)


def trisign_strongly_describes_order(trisign_to_compare, pair):
    a, b = pair
    """
    if sign_to_compare == 1:
        return a < b
    elif sign_to_compare == 0:
        return a == b
    elif sign_to_compare == -1:
        return a > b
    else:
        raise ValueError("sign.")
    """
    assert trisign_to_compare in {-1, 0, 1}
    return trisign_to_compare == compare(a, b)

assert all(trisign_strongly_describes_order(*testVals) for testVals in [(1,(5,6)),(0,(5,5)),(-1,(5,4))])
assert all((not trisign_strongly_describes_order(*testVals)) for testVals in [(1,(5,5)),(-1,(5,5)), (0,(5,6)),(-1,(5,6)), (1,(5,4)),(0,(5,4))])


def number_trisign_strongly_describes_order(number_to_compare, pair):
    return trisign_strongly_describes_order(trisign_of(number_to_compare), pair)
