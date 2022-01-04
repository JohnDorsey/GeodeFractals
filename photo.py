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

EXIT_CODES = {"success":0, "help":0, "no-args":0, "unknown-keyword-arg":20, "unknown-keyword-arg-operator":21, "unknown-keyword-arg-operation":22, "not-implemented-error": 50}

NOT_IMPLEMENTED_ERRLVL = 255






def gen_take_only(input_gen, count):
    for i in range(count):
        try:
            currentItem = next(input_gen)
        except StopIteration:
            return
        yield currentItem
    return
    
    
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

    


def preview_long_str(input_str):
    leftLen = 60
    rightLen = 60 
    if len(input_str) < 128:
        return input_str
    else:
        return (input_str[:leftLen] + "...{}chrs...".format(len(input_str)-leftLen-rightLen) + input_str[-rightLen:])
        
        
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


def higher_range(input_list, iteration_order=None):
    if iteration_order is not None:
        newInputList = [None for i in range(len(input_list))]
        for i, newLocation in enumerate(iteration_order):
            newInputList[newLocation] = input_list[i]
        for item in higher_range(newInputList, iteration_order=None):
            yield tuple(item[iteration_order[i]] for i in range(len(iteration_order)))
    settings_list = [None for i in range(len(input_list))]
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
        if newItem[2] < 0:
            raise NotImplementedError("this method can't test for range ends when moving backwards yet.")
        settings_list[i] = newItem
    counters = [settings_list[i][0] for i in range(len(input_list))]
    while True:
        yield tuple(counters)
        counters[0] += settings_list[0][2]
        if counters[0] >= settings_list[0][1]: # change to incorporate signed diffs.
            counters[0] = settings_list[0][0]
            for rolloverIndex in range(1, len(counters)):
                counters[rolloverIndex] += settings_list[rolloverIndex][2]
                if counters[rolloverIndex] >= settings_list[rolloverIndex][1]:
                    counters[rolloverIndex] = settings_list[rolloverIndex][0]
                    continue
                else:
                    break # no more rollovers should happen.
            else:
                return

assert [item for item in higher_range([(5,8), (1,4)])] == [(5,1), (6,1), (7,1), (5,2), (6,2), (7,2), (5,3), (6,3), (7,3)]


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
    for item in inputItemGen:
        if item in input_set:
            return False
    return True
            


def get_at_advanced(data_to_access, labeled_coords, access_order, bitcatted_axes={}, digested_axes={}, labeled_axis_sizes=None):
    if len(bitcatted_axes) > 0:
        assert shared_items_are_consecutive(access_order[::-1], bitcatted_axes), "bitcatted_axes much not have any gaps when compared to access order."
        raise NotImplementedError("can't do bitcatting yet.")
    if len(digested_axes) > 0:
        for digestedAxis in digested_axes:
            assert digestedAxis not in bitcatted_axes, "a bitcatted axis is stored as an integer, and can't be digested - bitcatting more than one axis is only possible by bitcatting both an axis and its parent axis."
        raise NotImplementedError("what goes here?")
    raise NotImplementedError()
            

def get_at(data_to_access, labeled_coords, access_order):
    if len(access_order) == 0:
        # return now because there is probably no more accessing (narrowing) to be done. This silently allows coords with nonsense components, though.
        return data_to_access
    if not hasattr(data_to_access, "__len__"):
        raise IndexError("the data can't be browsed here.")
    if len(data_to_access) == 0:
        raise IndexError("the data is empty here.")
        # return None
        
    if access_order[0] in labeled_coords:
        ac = labeled_coords[access_order[0]]
    else:
        ac = None
    
    if isinstance(ac, int):
        return get_at(data_to_access[ac], labeled_coords, access_order[1:])
    elif ac is None:
        ac = slice(None, None, None)
    else:
        assert isinstance(ac, slice), "invalid access coordinate provided."
    
    # this is where a change from an input access order to a different output access order might be made. Any coordinate components not specified in labled_coords could be swapped to change the orientation of the data. This would involve making the recursive calls to get_at include a new element in labeled_coords. let this added element be the index used in iteration.
    return [get_at(data_to_access_sub, labeled_coords, access_order[1:]) for data_to_access_sub in itertools.islice(data_to_access, ac.start, ac.stop, ac.step)]

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




def prepare_color(color_input, channel_depths=None):
    assert isinstance(channel_depths, (tuple, list))
    
    if isinstance(color_input, int):
        return prepare_color([color_input], channel_depths)  
    elif isinstance(color_input, (tuple, list)):
        if len(color_input) == len(channel_depths):
            workingColor = color_input
        elif len(color_input) < len(channel_depths):
            workingColor = (color_input + type(color_input)([0]*len(channel_depths)))[:len(channel_depths)]
        else:
            raise ValueError("the color is too long.")
    else:
        raise TypeError("bad color type: {}.".format(type(color_input)))
        
    for componentIndex, component in enumerate(workingColor):
        assert component >= 0
        assert component < 2**channel_depths[componentIndex]
        
    return workingColor





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
    

def gen_encode_pypng_row(color_seq, pypng_mode="RGB;8"):
    # assert isinstance(channel_depths, (tuple, list))
    # print("encoding row...")
    
    channelLetters, channelDepth = split_pypng_mode(pypng_mode)
    channelDepths = [channelDepth]*len(channelLetters)
    return ((item if item is not None else 0) for color in color_seq for item in prepare_color(color, channel_depths=channelDepths))
    


        
        

    

    
    
    
        
        
    
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
        

    
def pypng_streaming_save_square(filename, row_seq, height, pypng_mode="RGB;8"):
    assert height > 0, height
    assert filename.endswith(".png"), filename
    print("preparing to save file...")
    row_seq = gen_make_inexhaustible(row_seq) # prevent pypng from ever running out of lines.
    row_seq = gen_take_only(row_seq, height) # prevent pypng from having too many lines, which is not allowed.
    # row_seq = monitor_gen(row_seq, "(row_seq for this image)")
    print("initializing file...")
    image = png.from_array(row_seq, mode=pypng_mode, info={"height":height})
    finalFilename = unappend(filename, ".png") + "_" + str(time.time()) + ".png"
    print("saving file {}...".format(finalFilename))
    image.save(finalFilename)
    print("finished saving file {}.".format(finalFilename))
    
    
def pypng_streaming_save_squares(filename, row_seq, height, pypng_mode="RGB;8"):
    assert height > 0, height
    assert filename.endswith(".png"), filename
    peekableRowSeq = PeekableGenerator(row_seq)
    for i in itertools.count():
        try:
            print("peeking at row seq...")
            peekableRowSeq.peek_at_relative(0) # may raise StopIteration.
            print("done peeking.")
            pypng_streaming_save_square(unappend(filename, ".png")+"_{}px{}inseq.png".format(height, str(i).rjust(5,"0")), peekableRowSeq, height, pypng_mode=pypng_mode)
        except StopIteration:
            return
    assert False
    
    
    
    
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
            assumedHeight = len(eval(borrowedLine)) * keyword_args["row-subdivision"]
            peekableNotelessLineSource.fridge.clear()
            peekableNotelessLineSource.fridge.append(borrowedLine)
            break
    print("length is {}.".format(assumedHeight))
    
    filename, channelCount, channelDepth = keyword_args["output"], keyword_args["channel-count"], keyword_args["channel-depth"]
    pypngMode = format_pypng_mode(channel_count=channelCount, channel_depth=channelDepth)
    
    partialRowDataGen = (gen_encode_pypng_row(eval(line), pypng_mode=pypngMode) for line in peekableNotelessLineSource)
    if keyword_args["row-subdivision"] > 1:
        rowAsListGen = (list(item for rowPartItemGen in gen_take_only(gen_make_inexhaustible(partialRowDataGen), keyword_args["row-subdivision"]) for item in rowPartItemGen) for i in itertools.count())
    else:
        rowAsListGen = (list(rowAsGen) for rowAsGen in partialRowDataGen)
    # rowAsListGen = monitor_gen(rowAsListGen, "rowAsListGen")
    pypng_streaming_save_squares(filename, rowAsListGen, assumedHeight, pypng_mode=pypngMode)
    
    
    
    
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
                previousValueType = type(kwargs_to_edit[keyword_arg_name])
                if isinstance(previousValueType, (list, tuple, set, dict)):
                    raise NotImplementedError("can't fix that type.")
                conversionMethod = previousValueType # to preserve type of old value when replacing it with new one!
                kwargs_to_edit[keyword_arg_name] = conversionMethod(unprepend(operationStr, "="))
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

    if keyword_args["output"] is None or keyword_args["output"] == "":
        keyword_args["output"] = nonkeyword_args.popleft()
    
    cli_validate_args(nonkeyword_args, keyword_args)

    if nonkeyword_args[0] == "-":
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

keyword_args = {"output":"", "access-order": "yxc", "swizzle": None, "row-subdivision":1, "channel-count":3, "channel-depth":8} #"untitled{}.png".format(time.time())

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
    




