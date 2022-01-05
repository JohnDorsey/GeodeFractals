#!/usr/bin/python3


"""
    todo:
        -core:
            -replace builtin eval with a custom evaluator that has good error handling and no size limit.
        -etc:
            -accept pam files as input and as an output format.
            -user-defined kernels:
                -transform data in transit to another application.
                -output in multiple resolutions:
                    -use threads around pypng image.save.
                    -use subprocesses.
"""

import sys

print(sys.argv[0] + " started.")

import math
import itertools
import time
import collections
import copy

generator = type((i for i in range(1)))
    
import png

EXIT_CODES = {"success":0, "help":0, "no-args":0, "unknown-keyword-arg":20, "unknown-keyword-arg-operator":21, "unknown-keyword-arg-operation":22, "not-implemented-error": 50, "crash":51}



def assert_equal(thing0, thing1):
    assert thing0 == thing1, "{} does not equal {}.".format(thing0, thing1)

def assure_less_than(thing0, thing1):
    assert thing0 < thing1, "{} is not less than {}.".format(thing0, thing1)
    return thing0


def gen_take_only(input_gen, count):
    for i in range(count):
        try:
            currentItem = next(input_gen)
        except StopIteration:
            return
        yield currentItem
    return
    


def preview_long_str(input_str):
    leftLen = 60
    rightLen = 60 
    if len(input_str) < 128:
        return input_str
    else:
        return (input_str[:leftLen] + "...{}chrs...".format(len(input_str)-leftLen-rightLen) + input_str[-rightLen:])
        
    
    
def assure_length_is(input_container, length):
    assert len(input_container) == length, "the input container {} is {} items long, not the required {}.".format(preview_long_str(str(input_container)), len(input_container), length)
    return input_container
    
def assure_type_is(input_object, type_):
    assert type(input_object) == type_, type(input_object)
    return input_object

    
    
def gen_make_inexhaustible(input_gen):
    i, item = 0, None
    for item in input_gen:
        i += 1
        yield item
    print("warning: drawing from inexhaustible generator!")
    if i == 0:
        assert item is None
        print("warning: this inexhaustible generator had no items to use as templates!")
    while True:
        # yield copy.deepcopy(item)
        yield item


def unappend(string, suffix):
    assert string.endswith(suffix), "unappend is impossible for these inputs."
    result = string[:-len(suffix)]
    assert result + suffix == string
    return result
    
    
def unprepend(string, prefix):
    assert string.startswith(prefix), "unprepend is impossible for these inputs."
    result = string[len(prefix):]
    assert prefix + result == string
    return result

    


        
def monitor_gen(input_gen, nickname):
    print("{} is being monitored.".format(nickname))
    for i, item in enumerate(input_gen):
        print("{} provided item {}: {}.".format(nickname, i, preview_long_str(str(item))))
        yield item
        print("{} is being asked for another item.".format(nickname))


def measure_time(input_fun):
    def alt_fun(*args, **kwargs):
        startTime=time.time()
        input_fun(*args, **kwargs)
        endTime=time.time()
        totalTime = endTime-startTime
        print("took {} seconds ({} minutes).".format(totalTime, totalTime/60))
    return alt_fun

    
    
    
"""
def split_right(string, delimiter):
     return [item[::-1] for item in string[::-1].split(delimiter[::-1])[::-1]]
     
assert split_right("abc","b") == ["a","c"]
assert split_right("abbbc","bb") == ["ab","c"]

    
def rightmost_split(string, delimiter):
    splitResult = split_right(string, delimiter)
    if len(splitResult) in {1,2}:
        return splitResult
    else:
        assert len(splitResult) > 2
        return [delimiter.join(splitResult[:-1]), splitResult[-1]]
"""

def split_once(string, delimiter):
    result = string.split(delimiter)
    assert len(result) == 2
    return result
    

def product(input_seq):
    result = 1
    for item in input_seq:
        result *= item
    return result


def shape(data_to_test):
    result = []
    while hasattr(data_to_test, "__len__"):
        result.append(len(data_to_test))
        if result[-1] == 0:
            break
        data_to_test = data_to_test[0]
    return result
    
    
def labled_shape(data_to_test, access_order):
    result = dict()
    while hasattr(data_to_test, "__len__"):
        assert access_order[0] not in result
        result[access_order[0]] = len(data_to_test)
        data_to_test, access_order = data_to_test[0], access_order[1:]
    return result


def trisign(value):
    """
    if value < 0:
        return -1
    elif value > 0:
        return 1
    else:
        assert value == 0
        return 0
    """
    return compare(0, value)
        
def compare(a, b):
    if a < b:
        return 1
    elif a > b:
        return -1
    else:
        assert a == b
        return 0


def number_trisign_weakly_describes_order(a, b, number_to_compare):
    return trisign_weakly_describes_order(a, b, trisign(number_to_compare))

def trisign_weakly_describes_order(a, b, sign_to_compare):
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
    assert sign_to_compare in {-1, 0, 1}
    comparison = compare(a, b)
    if comparison == 0:
        return True
    elif sign_to_compare == 0:
        return False
    return sign_to_compare == comparison
    
assert all(trisign_weakly_describes_order(*testVals) for testVals in [(5,6,1),(5,5,1),(5,5,0),(5,5,-1),(5,4,-1)])
assert all((not trisign_weakly_describes_order(*testVals)) for testVals in [(5,6,0),(5,6,-1),(5,4,1),(5,4,0)])


def number_trisign_strongly_describes_order(a, b, number_to_compare):
    return trisign_strongly_describes_order(a, b, trisign(number_to_compare))

def trisign_strongly_describes_order(a, b, sign_to_compare):
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
    assert sign_to_compare in {-1, 0, 1}
    return sign_to_compare == compare(a, b)

assert all(trisign_strongly_describes_order(*testVals) for testVals in [(5,6,1),(5,5,0),(5,4,-1)])
assert all((not trisign_strongly_describes_order(*testVals)) for testVals in [(5,5,1),(5,5,-1), (5,6,0),(5,6,-1), (5,4,1),(5,4,0)])


def higher_range(input_list, iteration_order=None):
    if iteration_order is not None:
        newInputList = [None for i in range(len(input_list))]
        for i, newLocation in enumerate(iteration_order):
            newInputList[newLocation] = input_list[i]
        for item in higher_range(newInputList, iteration_order=None):
            yield tuple(item[iteration_order[i]] for i in range(len(iteration_order)))
    settings_list = [None for i in range(len(input_list))]
    
    # validate and expand settings:
    for i, item in enumerate(input_list):
        newItem = None
        if type(item) == int:
            newItem = (0,item,1)
        elif type(item) == tuple:
            if len(item) == 2:
                newItem = item + (1,)
            elif len(item) == 3:
                newItem = item
            else:
                raise ValueError("wrong tuple length.")
        assert newItem[2] != 0
        if newItem[2] < 0:
            raise NotImplementedError("this method can't test for range ends when moving backwards yet.")
        settings_list[i] = newItem
    assert None not in settings_list
        
    counters = [settings_list[i][0] for i in range(len(input_list))]
    while True:
        yield tuple(counters)
        counters[0] += settings_list[0][2]
        #if (counters[0] >= settings_list[0][1]): # change to incorporate signed diffs.
        if number_trisign_weakly_describes_order(settings_list[0][1], counters[0], settings_list[0][2]):
            counters[0] = settings_list[0][0]
            for rolloverIndex in range(1, len(counters)):
                counters[rolloverIndex] += settings_list[rolloverIndex][2]
                if number_trisign_weakly_describes_order(settings_list[rolloverIndex][1], counters[rolloverIndex], settings_list[rolloverIndex][2]):
                    counters[rolloverIndex] = settings_list[rolloverIndex][0]
                    continue
                else:
                    break # no more rollovers should happen.
            else:
                return
    assert False

assert_equal([item for item in higher_range([(5,8), (1,4)])], [(5,1), (6,1), (7,1), (5,2), (6,2), (7,2), (5,3), (6,3), (7,3)])


def shared_items_are_consecutive(input_list, input_set, require_immediate_start=False):
    inputItemGen = iter(input_list)
    for item in inputItemGen:
        if item not in input_set:
            if require_immediate_start:
                return False
        else:
            break
    for item in inputItemGen:
        # it doesn't matter how long the run of matches lasts.
        # zero matches in this loop means a match run length of one, where the one match was encountered in the first loop.
        if item not in input_set:
            break
    for item in inputItemGen: # make sure there are no _more_ matches.
        if item in input_set:
            return False
    return True
            
assert shared_items_are_consecutive("abcdefg", {"b","c","d"}) == True
assert shared_items_are_consecutive("abcdefg", {"b","c","d"}, require_immediate_start=True) == False
assert shared_items_are_consecutive("bcdefg", {"b","c","d"}, require_immediate_start=True) == True

"""
def get_shared_value(input_data):
    inputItemGen = iter(input_data)
    sharedValue = next(inputItemGen)
    for item in inputItemGen:
        assert item is not None, "can't be None."
        if item != sharedValue:
            return None
    return sharedValue

"""
"""
def gen_assuredly_same_group(input_data, key_fun):
    inputItemGen = iter(input_data)
    firstItem = next(inputItemGen)
    sharedGroupID = key_fun(firstItem)
    yield (sharedGroupID, firstItem)
    ...
"""

def gen_assuredly_in_group(input_data, key_fun, key):
    for item in input_data:
        assert key_fun(item) == key, "item {} in group {} is not in group {}.".format(item, key_fun(item), key)
        yield item
    
def flatten_and_assure_axial_uniform_depth(input_data):
    inputItemGen = iter(input_data)
    firstItem = next(inputItemGen)
    isEnterable = hasattr(firstItem, "__iter__")
    validatedItemGen = itertools.chain([firstItem], gen_assuredly_in_group(inputItemGen, (lambda testItem: hasattr(testItem, "__iter__")), isEnterable))
    if isEnterable:
        for item in validatedItemGen:
            for subItem in flatten_and_assure_axial_uniform_depth(item):
                yield subItem
    else:
        for item in validatedItemGen:
            yield item
        
    """
    if isEnterable:
        for item in inputItemGen:
            for subItem in flatten_uniform(item):
                yield subItem
    else:
        for item in inputItemGen:
            assert not hasattr(item, "__iter__")
            ...
    yield firstItem
    """
    

def flatten(input_data):
    for item in input_data:
        if hasattr(item, "__iter__"):
            yield flatten(item)
        else:
            yield item


def encode_flat_bitcat(input_data, item_bit_depth):
    result = 0
    itemValueRange = 2**item_bit_depth
    for item in input_data:
        assert isinstance(item, int), type(item)
        assert 0 <= item < itemValueRange, (item, itemValueRange)
        result *= itemValueRange
        result += item
    return result
    
assert_equal(encode_flat_bitcat([7, 6, 5, 4, 3, 2, 1, 0, 1, 2], 3), int("111_110_101_100_011_010_001_000_001_010", 2))
assert_equal(encode_flat_bitcat([6,7]*10, 3), int("110111"*10, 2))



def encode_deep_bitcat(input_data, leaf_bit_depth):
    itemGen = gen_assuredly_in_group(flatten_and_assure_axial_uniform_depth(input_data), (lambda testItem: isinstance(testItem, int)), True)
    return encode_flat_bitcat(itemGen, leaf_bit_depth)
    
assert_equal(encode_deep_bitcat([(7, 6), [(5, 4), (3, 2)], (1, 0), (1, 2)], 3), int("111_110_101_100_011_010_001_000_001_010", 2))




def decode_flat_bitcat(input_data, item_bit_depth, count=None):
    result = []
    itemValueRange = 2**item_bit_depth
    while input_data > 0:
        result.append(input_data % itemValueRange)
        input_data //= itemValueRange
    if count is not None:
        while len(result) < count:
            result.append(0)
    for item in result:
        assert item.bit_length() <= item_bit_depth, (item, result, input_data)
    return result[::-1]

testArr = [(i**3)%16 for i in range(64)]
assert_equal(decode_flat_bitcat(encode_flat_bitcat(testArr, 16), 16, count=len(testArr)), testArr)
del testArr


def gen_accumulate_product(input_seq):
    return itertools.accumulate(input_seq, lambda a, b: a*b)



def get_in_uniform_flat_bitcat(input_data, item_bit_length=None, significance_index=None):
    assert item_bit_length >= 1
    assert significance_index is not None
    # if item_count is not None and item_bit_length is not None:
    #     assert input_data.bit_length() < item_count*item_bit_length
    # mask = (2**item_bit_length - 1) * (2**(item_bit_length*significance_index))
    mask = 2**(item_bit_length*(significance_index+1)) - 1
    result = (input_data & mask) // (2**(item_bit_length*significance_index))
    return result
    
testArr = [0,0,1,16,64,192,255,254,128,127,126]
testNum = encode_flat_bitcat(testArr, 8)
assert_equal([get_in_uniform_flat_bitcat(testNum, item_bit_length=8, significance_index=len(testArr)-i-1) for i in range(len(testArr))], testArr)
del testArr, testNum


def get_in_uniform_deep_bitcat(input_data, labeled_coords, access_order, labeled_axis_sizes, leaf_bit_length):
    flatIndexRange = product(labeled_axis_sizes[axisLabel] for axisLabel in access_order)
    # axisLabelAndScopeSizeGen = itertools.accumulate(((axisLabel, labeled_axis_sizes[axisLabel]) for axisLabel in access_order[::-1]), lambda workingPair,)...
    axisSizeGen = (labeled_axis_sizes[axisLabel] for axisLabel in access_order[::-1])
    axisLabelAndWorthGen = zip(access_order[::-1], gen_accumulate_product(itertools.chain([1], axisSizeGen)))
    flatIndex = sum(labeled_coords[axisLabel]*axisWorth for axisLabel, axisWorth in axisLabelAndWorthGen)
    flatSignificanceIndex = flatIndexRange - flatIndex - 1
    return get_in_uniform_flat_bitcat(input_data, item_bit_length=leaf_bit_length, significance_index=flatSignificanceIndex)
    
testArr = [[0,0,1], [16,64,192], [255,254,128], [127,126,1]]
testNum = encode_deep_bitcat(testArr, 8)
assert_equal([[get_in_uniform_deep_bitcat(testNum, {"x":x, "y":y}, "yx", {"y":4, "x":3}, leaf_bit_length=8) for x in range(3)] for y in range(4)], testArr)
del testArr, testNum
    

def get_at_advanced(input_data, labeled_coords, access_order, bitcatted_axes={}, digested_axes={}, labeled_axis_sizes=None):
    if len(bitcatted_axes) > 0:
        assert shared_items_are_consecutive(access_order[::-1], bitcatted_axes, require_immediate_start=True), "bitcatted_axes much not have any gaps when compared to access order."
        assert labeled_axis_sizes is not None, "axis sizes must be provided to undo bit concatenation."
        assert all(label in labeled_axis_sizes for label in bitcatted_axes), "not enough info."
        bitcatInt = get_at_advanced(input_data, labeled_coords, access_order[:-len(bitcatted_axes)], digested_axes=digested_axes, labeled_axis_sizes=labeled_axis_sizes)
        raise NotImplementedError("not finished.")
    if len(digested_axes) > 0:
        for digestedAxis in digested_axes:
            assert digestedAxis not in bitcatted_axes, "a bitcatted axis is stored as an integer, and can't be digested - bitcatting more than one axis is only possible by bitcatting both an axis and its parent axis."
        raise NotImplementedError("what goes here?")
    raise NotImplementedError()
            

def get_at(input_data, labeled_coords, access_order):
    if len(access_order) == 0:
        # return now because there is probably no more accessing (narrowing) to be done. This silently allows coords with nonsense components, though.
        return input_data
    if not hasattr(input_data, "__len__"):
        raise IndexError("the data can't be browsed here.")
    if len(input_data) == 0:
        raise IndexError("the data is empty here.")
        # return None
        
    if access_order[0] in labeled_coords:
        ac = labeled_coords[access_order[0]]
    else:
        ac = None
    
    if isinstance(ac, int):
        return get_at(input_data[ac], labeled_coords, access_order[1:])
    elif ac is None:
        ac = slice(None, None, None)
    else:
        assert isinstance(ac, slice), "invalid access coordinate provided."
    
    # this is where a change from an input access order to a different output access order might be made. Any coordinate components not specified in labled_coords could be swapped to change the orientation of the data. This would involve making the recursive calls to get_at include a new element in labeled_coords. let this added element be the index used in iteration.
    return [get_at(input_data_sub, labeled_coords, access_order[1:]) for input_data_sub in itertools.islice(input_data, ac.start, ac.stop, ac.step)]

assert get_at([[1,2,3],[4,5,6],[7,8,9]], {"x":2, "y":1}, "yx") == 6
assert get_at([[1,2,3],[4,5,6],[7,8,9]], {"x":2}, "yx") == [3,6,9]

assert get_at(([[1,2,3],[4,5,6],[7,8,9]], [[10,20,30],[40,50,60],[70,80,90]]), {"x":0, "y":2, "c":1}, "cyx") == 70
assert get_at(([[1,2,3],[4,5,6],[7,8,9]], [[10,20,30],[40,50,60],[70,80,90]]), {"x":0, "y":2}, "cyx") == [7,70]


"""
def slice_to_seq(input_slice):
    args = [input_slice.start, input_slice.stop, input_slice.step]
    if args[0] is None:
        args[0] = 0
    if args[1] is None:
        return itertools.count(args[0], args[2])
    else:
        return range(*args)
        
def are_anagrams(dataA, dataB):
    if len(dataA) != len(dataB):
        return False
    if dataA == dataB:
        return True
    return (sorted(dataA) == sorted(dataB))
    

def get_formatted(input_data, labeled_coords, input_access_order, output_access_order=None, labeled_output_types=None):
    # includes some slow assertions involving sorting.
    if output_access_order is None:
        output_access_order = input_access_order
    if len(output_access_order) < len(input_access_order):
        output_access_order += [item for item in input_access_order if item not in output_access_order]
    assert are_anagrams(input_access_order, output_access_order)
    
    if not isinstance(labeled_coords, dict):
        raise TypeError("labeled_coords must be dict.")
        
    if output_access_order[0] not in labeled_coords:
        labeled_coords[output_access_order[0]] = slice(None,None,None)
    assert output_access_order[0] in labeled_coords
    
    if output_access_order[0] == input_access_order[0]:
        perCurrentCoordGetter = lambda currentCoord: get_formatted(input_data[currentCoord], labeled_coords, input_access_order[1:], output_access_order=output_access_order[1:])
        currentCoordSrc = labeled_coords[input_access_order[0]]
        if isinstance(currentCoordSrc, slice):
            currentCoordSeq = slice_to_seq(currentCoordSrc)
            resultGen = (perCurrentCoordGetter(currentCoordB) for currentCoordB in currentCoordSeq)
            resultOutputType = list if labeled_output_types is None else (list if output_access_order[0] not in labeled_output_types else labeled_output_types[output_access_order[0]])
            if resultOutputType is generator:
                return resultGen
            else:
                return resultOutputType(resultGen)
        else:
            assert isinstance(currentCoordSrc, int), "invalid coordinate type."
            ...
    else:
        ...
"""



"""
def prepare_color(color_input, channel_max_values=None):
    assert isinstance(channel_max_values, (tuple, list))
    
    workingColor = color_input
    
    if isinstance(workingColor, int):
        workingColor = [workingColor]
    assert isinstance(workingColor, (list, tuple))
    assert len(workingColor) <= len(channel_max_values)
    
    if len(workingColor) < len(channel_max_values):
        workingColor = workingColor + type(workingColor)([0]*(len(channel_max_values) - len(workingColor)))
    assert len(workingColor) == len(channel_max_values)
    
    for componentIndex, component in enumerate(workingColor):
        assert component >= 0
        assert component <= channel_max_values[componentIndex], "at index {} in the color {} made from the input {}, the value {} is not less than the maximum {} in {}.".format(componentIndex, workingColor, color_input, component, channel_max_values[componentIndex], channel_max_values)
        
    return workingColor

assert_equal(tuple(prepare_color((255, 0, 0), channel_max_values=(255, 255, 255, 255))), (255, 0, 0, 0))
assert_equal(tuple(prepare_color(255, channel_max_values=(255, 255, 255, 255))), (255, 0, 0, 0))
"""


def split_pypng_mode(pypng_mode):
    if ";" not in pypng_mode:
        pypng_mode += ";8"
    channelLetters, bitDepth = split_once(pypng_mode, ";")
    bitDepth = int(bitDepth)
    return [channelLetters, bitDepth]


"""

def gen_bytes_in_shorts(shorts_seq):
    # this should be replaced by a general method for converting between word sizes.
    for item in shorts_seq:
        assert isinstance(item, int)
        assert item >= 0
        assert item < 65536
        yield item // 256
        yield item % 256
        
def color_to_pypng_byteints(input_color, pypng_mode="RGB;8"):
    # this might not be needed at all.
    channelLetters, bitDepth = split_pypng_mode(pypng_mode)
    
    assert len(input_color) == len(channelLetters), "bad color length."
    
    if bitDepth == 16:
        return gen_bytes_in_shorts(input_color)
    elif bitDepth == 8:
        for item in input_color:
            assert 0 <= item < 256
            yield item
    else:
        raise NotImplementedError("can't convert at this bit depth to bytes for encoding.")
"""


def channel_count_to_pypng_color_letters(count):
    assert count > 0
    return ["L", "LA", "RGB", "RGBA"][count-1]
    
def format_pypng_mode(channel_count=None, channel_depth=None):
    assert (channel_count is not None) and (channel_depth is not None)
    assert 1 <= channel_count <= 4, "unsupported channel count."
    assert 1 <= channel_depth <= 16, "unsupported channel bit depth."
    return channel_count_to_pypng_color_letters(channel_count) + ";" + str(channel_depth)
    
"""
def gen_encode_pypng_row(color_seq, pypng_mode="RGB;8"):
    # assert isinstance(channel_depths, (tuple, list))
    # print("encoding row...")
    
    channelLetters, channelDepth = split_pypng_mode(pypng_mode)
    channelCount = len(channelLetters)
    assert channelCount == 3, "not implemented."
    channelMaxValues = [(2**channelDepth)-1]*channelCount
    result = ((item if item is not None else 0) for color in color_seq for item in assure_length_is(list(prepare_color(color, channel_max_values=channelMaxValues)), channelCount))
    return result
"""

        
        

    

    
    
    
        
        
    
def gen_file_lines(source_file=sys.stdin):
        
    for i in itertools.count():
        print("waiting for line {}.".format(i))
        nextLine = source_file.readline()
        """
        nextLineChars = []
        while True:
            newChar = sys.stdin.read(1)
            #print(newChar,end="")
            if newChar == "\n":
                break
            nextLineChars.append(newChar)
        nextLine = "".join(nextLineChars)
        """
        if nextLine.startswith("#"):
            print("line {} is {}.".format(i, nextLine[:-1]))
        else:
            print("line {} is {}.".format(i, preview_long_str(nextLine[:-1])))
        
        # if nextLine.startswith("#"):
        #     continue
            
        if len(nextLine) == 0:
            print("line length zero! ending!")
            return
        if nextLine == "STOP":
            print("line says STOP! ending!")
            return
        if nextLine.startswith("STOP"):
            print("line starts with STOP! ending!")
            return
        #if i == count:
        #    print("line will not be supplied")
        # print("yielding plaintext line.")
        assert nextLine.endswith("\n"), "it actually ends {}.".format(nextLine[-8:])
        yield nextLine[:-1]

        
class PeekableGenerator:
    # maybe this shouldn't exist. maybe it should be replaced with itertools.tee.
    def __init__(self, source_gen):
        self.source_gen = source_gen
        self.fridge = collections.deque([])
    
    def _unlock_once(self):
        result = next(self.source_gen)
        self.fridge.append(result)
        return result
        
    def peek_at_relative(self, index):
        assert index >= 0
        while len(self.fridge) <= index:
            self._unlock_once()
        return self.fridge[index]
        
    def __next__(self):
        if len(self.fridge) != 0:
            result = self.fridge.popleft()
            return result
        else:
            return next(self.source_gen)
            
    def next(self): # for python2 support.
        return self.__next__()
    
    def __iter__(self):
        return self
        

    
def pypng_streaming_save_square(filename, row_seq, height=None, pypng_mode="RGB;8"):
    assert height > 0, height
    assert filename.endswith(".png"), filename
    print("preparing to save file...")
    row_seq = gen_make_inexhaustible(row_seq) # prevent pypng from ever running out of lines.
    row_seq = gen_take_only(row_seq, height) # prevent pypng from having too many lines, which is not allowed.
    # row_seq = monitor_gen(row_seq, "(row_seq for this image)")
    print("initializing file...")
    image = png.from_array(row_seq, mode=pypng_mode, info={"width":height, "height":height})
    finalFilename = unappend(filename, ".png") + "_" + str(time.time()) + ".png"
    print("finished initializing file.")
    # return image
    print("saving file {}...".format(finalFilename))
    image.save(finalFilename)
    print("finished saving file {}.".format(finalFilename))
    
    
def pypng_streaming_save_squares(filename, row_seq, height=None, pypng_mode="RGB;8"):
    assert height > 0, height
    assert filename.endswith(".png"), filename
    
    peekableRowSeq = PeekableGenerator(row_seq)
    
    for i in itertools.count():
        try:
            print("peeking at row seq...")
            peekedRow = peekableRowSeq.peek_at_relative(0) # may raise StopIteration.
            assert isinstance(peekedRow, list)
            print("done peeking.")
            try:
                pypng_streaming_save_square(unappend(filename, ".png") + "_{}px{}inseq.png".format(height, str(i).rjust(5,"0")), peekableRowSeq, height=height, pypng_mode=pypng_mode)
            except TypeError as e:
                sys.stderr.write("Exception while saving: {}.\n".format(e))
                sys.stderr.write("The most recently peeked row looked like {} and had {} items.\n".format(preview_long_str(str(peekedRow)), len(peekedRow)))
                exit(EXIT_CODES["crash"])
        except StopIteration:
            return
    assert False
    



    
def decode_input_pixel_bitcat(input_int):
    assert keyword_args["bitcatted-axes"] == {"c"}, "this method should not be used! settings are {}.".format(keyword_args)
    
    result = tuple(decode_flat_bitcat(input_int, keyword_args["channel-depth"], count=keyword_args["channel-count"]))
    assert len(result) == keyword_args["channel-count"]
    assert all(0 <= item < 2**keyword_args["channel-depth"] for item in result)
    return result

        
def validate_pypng_flat_row(input_pypng_flat_row, expected_width):
    """
    if not len(input_pypng_flat_row) == (expected_width * keyword_args["channel-count"]):
        return False
    for item in input_pypng_flat_row:
        if not (type(item) == int and item >= 0 and item < 2**keyword_args["channel-depth"]):
            return False
    return True
    """
    assure_length_is(input_pypng_flat_row, (expected_width * keyword_args["channel-count"]))
    assert min(input_pypng_flat_row) >= 0
    assert max(input_pypng_flat_row) < 2**keyword_args["channel-depth"]
    assert all((type(item) == int) for item in input_pypng_flat_row)
    
    
def input_row_to_pypng_flat_row(input_row, expected_width):
    if len(keyword_args["bitcatted-axes"]) > 0:
        if keyword_args["access-order"] != "yxc":
            raise NotImplementedError()
        if len(keyword_args["bitcatted-axes"]) > 1:
            raise NotImplementedError()
        pypngFlatRow = [component for bitcatNum in input_row for component in decode_input_pixel_bitcat(bitcatNum)]
    else:
        pypngFlatRow = [component for pixel in input_row for component in pixel]
    validate_pypng_flat_row(pypngFlatRow, expected_width), (preview_long_str(str(pypngFlatRow)), keyword_args)
    return pypngFlatRow
    
    
@measure_time
def run_streaming():
    
    simpleLineSource = gen_file_lines()
    notelessLineSource = (item for item in simpleLineSource if not item.startswith("#"))
    
    peekableNotelessLineSource = PeekableGenerator(notelessLineSource)
    for i in itertools.count():
        borrowedLine = peekableNotelessLineSource.peek_at_relative(i)
        if borrowedLine.startswith("ARGUMENT"):
            load_cli_arg(unprepend(borrowedLine, "ARGUMENT "), nonkeyword_args, keyword_args)
            cli_validate_args(nonkeyword_args, keyword_args)
        else:
            peekedWidth = len(eval(borrowedLine)) * keyword_args["row-subdivision"]
            peekableNotelessLineSource.fridge.clear()
            peekableNotelessLineSource.fridge.append(borrowedLine)
            break
    print("peekedWidth is {}.".format(peekedWidth))
    
    print("encoding will soon start. The settings are: {}.".format(keyword_args))
    
    partialRowDataGen = (eval(line) for line in peekableNotelessLineSource)
    
    if keyword_args["row-subdivision"] > 1:
        rowAsListGen = (list(item for rowPartItemGen in gen_take_only(gen_make_inexhaustible(partialRowDataGen), keyword_args["row-subdivision"]) for item in rowPartItemGen) for i in itertools.count())
    else:
        assert keyword_args["row-subdivision"] == 1
        rowAsListGen = (list(rowAsGen) for rowAsGen in partialRowDataGen)
            
    rowAsListGen = (input_row_to_pypng_flat_row(inputRow, peekedWidth) for inputRow in rowAsListGen)
        
    pypng_streaming_save_squares(keyword_args["output"], rowAsListGen, height=peekedWidth, pypng_mode=format_pypng_mode(channel_count=keyword_args["channel-count"], channel_depth=keyword_args["channel-depth"]))
    
    
    
    
def get_after_match(text_to_match, arg_to_test):
    if arg_to_test.startswith(text_to_match):
        return arg_to_test[len(text_to_match):]
        
def get_after_keyword_match(name_to_match, arg_to_test, separator="="):
    return get_after_match("--" + name_to_match + separator, arg_to_test)









def overwrite_matches_left(input_list, index, test_value, new_value):
    # returns last (leftmost) changed index.
    changeCount = 0
    for i in range(index, -1, -1):
        if input_list[i] == test_value:
            input_list[i] = new_value
            changeCount += 1
        else:
            if changeCount > 0:
                return i + 1
            else:
                return None
                
def trim_floats_in_str(input_str):
    digits = {str(i) for i in range(10)}
    charList = [char for char in input_str]
    digitRunLength = None
    for i, char in enumerate(charList):
        if char == ".":
            digitRunLength = 0
        elif digitRunLength is not None:
            if char in digits:
                digitRunLength += 1
            else:
                lastChangedIndex = overwrite_matches_left(charList, i-1, "0", "")
                if lastChangedIndex is not None:
                    assert lastChangedIndex > 0
                    assert charList[lastChangedIndex] == ""
                    if charList[lastChangedIndex - 1] == ".":
                        charList[lastChangedIndex] = "0" # undo that change.
                digitRunLength = None
    return "".join(charList)
assert trim_floats_in_str("helloc_abb_z0_1024itr2bisuper_clearonout_swapiterorder_seedbias(0.000000to0.000000and0.000000to-2.000000i)_color(0.250000pow16.000000scale8bitclamp)_512px00002inseq_1641234011.8041685.png") == "helloc_abb_z0_1024itr2bisuper_clearonout_swapiterorder_seedbias(0.0to0.0and0.0to-2.0i)_color(0.25pow16.0scale8bitclamp)_512px00002inseq_1641234011.8041685.png"
            

cli_arg_transformer_funs = {"trimfloats": trim_floats_in_str}


def load_cli_arg(arg_str, args_to_edit, kwargs_to_edit):
    # def fail():
    
    if arg_str.startswith("--"):
    
        if arg_str == "--help":
            print(HELP_STRING)
            exit(EXIT_CODES["help"])
            
        for keyword_arg_name in kwargs_to_edit.keys():
            operationStr = get_after_keyword_match(keyword_arg_name, arg_str, separator="")
            if operationStr is None:
                continue
            if operationStr.startswith("="):
                previousValue = kwargs_to_edit[keyword_arg_name]
                previousValueType = type(previousValue)
                newValueString = unprepend(operationStr, "=")
                if previousValueType in {str, int}:
                    kwargs_to_edit[keyword_arg_name] = previousValueType(newValueString)
                elif previousValueType in {list, tuple, set}:
                    for item in previousValue:
                        if type(item) != str:
                            raise NotImplementedError("can't regenerate any item type but str.")
                    newValueAsList = [item for item in newValueString.split(",") if item != ""]
                    kwargs_to_edit[keyword_arg_name] = previousValueType(newValueAsList)
                elif previousValueType in {dict}:
                    raise NotImplementedError("can't modify arg of that type.")
                else:
                    raise NotImplementedError("cant' modify arg of unrecognized type.")
            elif operationStr.startswith("+="):
                kwargs_to_edit[keyword_arg_name] += unprepend(operationStr, "+=")
            elif operationStr.startswith("."):
                transformDescStr = unprepend(operationStr, ".")
                if transformDescStr not in cli_arg_transformer_funs:
                    print("unknown keyword argument operation using '.'.")
                    exit(EXIT_CODES["unknown-keyword-arg-operation"])
                transformerFun = cli_arg_transformer_funs[transformDescStr]
                kwargs_to_edit[keyword_arg_name] = transformerFun(kwargs_to_edit[keyword_arg_name])
            else:
                print("unknown operator {} in argument description {}.".format(operationStr, arg_str)) # ! fix format later?
                exit(EXIT_CODES["unknown-keyword-arg-operator"])
                
            assert kwargs_to_edit[keyword_arg_name] is not None, keyword_arg_name
            return True
            
        print("unknown option: {}".format(arg_str))
        exit(EXIT_CODES["unknown-keyword-arg"])
    else:
        args_to_edit.append(arg_str)
        
        
def cli_validate_args(args_to_validate, kwargs_to_validate):
    if kwargs_to_validate["swizzle"] is not None:
        raise NotImplementedError("swizzle")
    
    # assert kwargs_to_validate["output"].endswith(".png")
    assert len(args_to_validate) <= 2


def cli_main():
    if len(prog_args) == 0:
        print(USAGE_STRING)
        exit(EXIT_CODES["no-args"])
        
    for argStr in prog_args:
        load_cli_arg(argStr, nonkeyword_args, keyword_args)
        
    cli_validate_args(nonkeyword_args, keyword_args)

    if keyword_args["output"] in {None, ""}:
        keyword_args["output"] = nonkeyword_args.popleft()
    if keyword_args["input"] in {None, ""}:
        keyword_args["input"] = nonkeyword_args.popleft()
    
    cli_validate_args(nonkeyword_args, keyword_args)

    if keyword_args["input"] == "-":
        print("will run in streaming mode. settings: {}, {}.".format(nonkeyword_args, keyword_args))
        run_streaming()
        print("run_streaming is over.")
    else:
        raise ValueError("data must be streaming, use '-'.")

    print("exiting python.")
    exit(EXIT_CODES["success"])



prog_args = sys.argv[1:]

keyword_arg_descriptions = {
    "access-order": "yxc in whatever order they must be applied to access the smallest data item in the input data.",
    "swizzle": "[r][g][b][l][a], where each string position affects a corresponding output channel, and the letter at that position defines which input channel should be written to the output channel."
}  

keyword_args = {"input":"", "output":"", "access-order": "yxc", "bitcatted-axes":set(), "swizzle": None, "row-subdivision":1, "channel-count":3, "channel-depth":8} #"untitled{}.png".format(time.time())

nonkeyword_args = collections.deque([])

USAGE_STRING = "Usage: [OPTION] <FILE> <DATA>"
HELP_STRING = """
Create FILE png described by DATA.
if DATA is '-', all data will be read from stdin. Currently this requires that each line contains one row of pixel info. Lines starting with '#' will be printed, and not evaluated.

optional arguments:
--help displays this message.
there are some others but they aren't documented yet."""


        


if len(sys.argv[0]) > 0: # if being run as a command:
    cli_main()
else:
    print("Not in interactive mode.")
    




