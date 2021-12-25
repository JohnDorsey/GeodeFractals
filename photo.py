#!/usr/bin/python3

"""
todo:
  -core:
    -simplify. Make only streaming.
    -replace builtin eval with a custom evaluator that has good error handling and no size limit.
    -accept any arguments through stdin as well as the usual way.
    -pypy support.
  -etc:
    -support 16bit png output.
    -accept pam files as input and as an output format.
    -allow tiny pygame previews of a file under construction.
    -user-defined kernels:
      -transform data in transit to another application.
      -output in multiple resolutions.
"""


import sys
# print(sys.argv[0])
import math
import itertools
import time
import collections


    
import png

NOT_IMPLEMENTED_ERRLVL = 255


def measure_time(input_fun):
    def alt_fun(*args, **kwargs):
        startTime=time.time()
        input_fun(*args, **kwargs)
        endTime=time.time()
        totalTime = endTime-startTime
        print("took {} seconds ({} minutes).".format(totalTime, totalTime/60))
    return alt_fun


def gen_take_only(input_gen, count):
    for i in range(count):
        try:
            currentItem = next(input_gen)
        except StopIteration:
            return
        yield currentItem
    return
    
    
def gen_make_inexhaustible(input_gen):
    for item in input_gen:
        yield item
    while True:
        yield item


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
        if counters[0] >= settings_list[0][1]: #change to incorporate signed diffs.
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


    
def get_at(data_to_access, labled_coords, access_order, bitcatted_axes="", dissolved_axes="", labled_axis_sizes=None):
    if len(access_order) == 0:
        # return now because there is probably no more accessing (narrowing) to be done. This silently allows coords with nonsense components, though.
        return data_to_access
    if not hasattr(data_to_access, "__len__"):
        if access_order[0] in bitcatted_axes:
            raise NotImplementedError("currently can't undo bit concatenation.")
            exit(NOT_IMPLEMENTED_ERRLVL)
            #when implemented, it will require knowledge of the axis' max size.
            #also, bitcatting can only apply to axes that appear consecutively and immediately before the end of access_order.
        else:
            #return incomplete answer because narrowing can't continue. Maybe this should raise an exception.
            return data_to_access
    if len(data_to_access) == 0:
        #return incomplete answer because the data is empty here.
        return None
        
    if access_order[0] in labled_coords:
        ac = labled_coords[access_order[0]]
        return get_at(data_to_access[ac], labled_coords, access_order[1:])
    else:
        #this is where a change from an input access order to a different output access order might be made. Any coordinate components not specified in labled_coords could be swapped to change the orientation of the data. This would involve making the recursive calls to get_at include a new element in labled_coords. let this added element be the index used in iteration.
        if len(access_order) > 1 and access_order[1] in dissolved_axes:
            assert access_order[1] in labled_axis_sizes or access_order[0] in labled_axis_sizes
            raise NotImplementedError("currently can't handle dissolved axes.")
            exit(NOT_IMPLEMENTED_ERRLVL)
            #this is where formats like [[r g b r g b r g b ...]...] will be handled.
        else:
            return [get_at(data_to_access[i], labled_coords, access_order[1:], bitcatted_axes=bitcatted_axes, dissolved_axes=dissolved_axes, labled_axis_sizes=labled_axis_sizes) for i in range(len(data_to_access))]

assert get_at([[1,2,3],[4,5,6],[7,8,9]], {"x":2, "y":1}, "yx") == 6
assert get_at([[1,2,3],[4,5,6],[7,8,9]], {"x":2}, "yx") == [3,6,9]

assert get_at(([[1,2,3],[4,5,6],[7,8,9]], [[10,20,30],[40,50,60],[70,80,90]]), {"x":0, "y":2, "c":1}, "cyx") == 70
assert get_at(([[1,2,3],[4,5,6],[7,8,9]], [[10,20,30],[40,50,60],[70,80,90]]), {"x":0, "y":2}, "cyx") == [7,70]






def prepare_color(color_input, channel_depths):
    if type(color_input) in {tuple, list}:
        for componentIndex, component in enumerate(color_input):
            assert component >= 0
            assert component < 2**channel_depths[componentIndex]
        if len(color_input) == len(channel_depths):
            return color_input
        else:
            return (color_input + type(color_input)([0]*3))[:3]
    elif isinstance(color_input, int):
        assert 0 <= color_input
        assert color_input < 2**channel_depths[0]
        return (color_input, 0, 0)
    else:
        raise TypeError(str(type(color_input)))
        
    #elif isinstance(item, float):
    #    assert 0 <= item <= 1
    #    intVal = max(0, min(255, math.floor(item*256)))






def channel_count_to_pypng_color_mode(count):
    assert count > 0
    return ["l", "la", "rgb", "rgba"][count-1]

def encode_pypng_row(color_seq):
    def verifiedColor(color):
        if isinstance(color, tuple):
            assert len(color) == 3
            return color
        if isinstance(color, int):
            return (color, color, color)
        raise TypeError(color)
    return bytes([(item if item is not None else 0) for color in color_seq for item in verifiedColor(color)])
    


        
        

    
def run_nonstreaming(data, filename, library_name):
    labledDataShape = labled_shape(data, keyword_args["access-order"])
    #assert "c" in labledDataShape
    if library_name == "png":
        channel_depths = (8,)*(labledDataShape["c"] if "c" in labledDataShape else 3)
        #assert len(channel_depths) != 3
    else:
        assert library_name == "pygame"
        channel_depths = (8, 8, 8)
    canvas = Canvas((labledDataShape["x"], labledDataShape["y"], len(channel_depths)), library_name)
    apparentColorMode = channel_count_to_pypng_color_mode(len(channel_depths))
    for y in range(labledDataShape["y"]):
        for x in range(labledDataShape["x"]):
            pixelColorData = get_at(data, {"x":x, "y":y}, keyword_args["access-order"])
            pixelColor = prepare_color(pixelColorData, channel_depths)
            if keyword_args["swizzle"] is not None:
                pixelColor = tuple(pixelColor[apparentColorMode.index(channelKey)] for channelKey in keyword_args["swizzle"])
            canvas.write_pixel((x,y), pixelColor)
    canvas.save_as(filename)
    
    
    
def gen_stdin_lines():
    #i = 0
    for i in itertools.count():
        print("wait. ", end="")
        nextLine = sys.stdin.readline()
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
        print("line {} starts: {}.".format(i, nextLine[:128]))
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
        yield nextLine
        #i += 1

        
class PeekableGenerator:
    # this shouldn't exist. it should be replaced with itertools.tee.
    def __init__(self, source_gen):
        self.source_gen = source_gen
        self.fridge = collections.deque([])
    def peek(self):
        result = next(self.source_gen)
        self.fridge.append(result)
        return result
    def __next__(self):
        if len(self.fridge) != 0:
            result = self.fridge.popleft()
            return result
        else:
            return next(self.source_gen)
    def __iter__(self):
        return self
        
        

    
    
def pypng_streaming_save_square(filename, row_seq, height):
    row_seq = gen_make_inexhaustible(row_seq) # prevent pypng from ever running out of lines.
    row_seq = gen_take_only(row_seq, height) # fix issue where pypng complains about having more rows than it needs and crashes. Kinda weird but I still love you, pypng.
    image = png.from_array(row_seq, "RGB", info={"height":height})
    image.save(filename + "_" + str(time.time()) + ".png")
    
    
def pypng_streaming_save_squares(filename, row_seq, height):
    peekableRowSeq = PeekableGenerator(row_seq)
    for i in itertools.count():
        try:
            peekableRowSeq.peek() # may raise StopIteration.
            pypng_streaming_save_square(filename+"_{}px{}inseq".format(height, i), peekableRowSeq, height)
        except StopIteration:
            return
    assert False
    
    
@measure_time
def run_streaming(filename):
    simpleLineSource = gen_stdin_lines()
    notelessLineSource = (item for item in simpleLineSource if "#" not in item)
    
    peekableLineSource = PeekableGenerator(notelessLineSource)
    borrowedLine = peekableLineSource.peek()
    assumedHeight = len(eval(borrowedLine))
    peekableLineSource.fridge.clear()
    peekableLineSource.fridge.append(borrowedLine)
    print("length {}.".format(assumedHeight))
    
    #iterableSource = (encodePyPngRow(eval(line)) for source in [[stolenLine], lineSource] for line in source)
    iterableSource = (encode_pypng_row(eval(line)) for line in peekableLineSource)
    
    pypng_streaming_save_squares(filename, iterableSource, assumedHeight)
    
    
    
    
def get_after_match(text_to_match, arg_to_test):
    if arg_to_test.startswith(text_to_match):
        return arg_to_test[len(text_to_match):]
        
def get_after_keyword_match(name_to_match, arg_to_test):
    return get_after_match("--" + name_to_match + "=", arg_to_test)



prog_args = sys.argv[1:]

keyword_arg_descriptions = {
    "access-order": "yx[c] in whatever order they must be applied to access the smallest data item in the input data.",
    "swizzle": "[r][g][b][l][a], where each string position affects a corresponding output channel, and the letter at that position defines which input channel should be written to the output channel."
}  
keyword_args = {"access-order": "yxc", "swizzle": None}
# in the future, it will be possible to use a similar looking definition to specify flatter data.
# e.g.: 
#   "yxc" -> [[[y0x0c0, y0x0c1], [y0x1c0, y0x1c1]], [[y1x0c0...]...]].
#   "y(xc)" -> [[y0x0c0, y0x0c1, y0x1c0, y0x1c1], [y1x0c0...]].
#   "(yx)c" -> [[y0x0c0, y0x0c1], [y0x1c0, y0x1c1], [y1x0c0...]...]].
#   "(yxc)" -> [y0x0c0, y0x0c1, y0x1c0, y0x1c1, y1x0c0...].
#   keep in mind that no new operations are needed to make rows come in unbound groups of three for color channels - this is the same as "(yc)x".

nonoption_args = []

USAGE_STRING = "Usage: [OPTION] <FILE> <DATA>"
HELP_STRING = """
Create FILE png described by DATA.
if DATA is '-', all data will be read from stdin. Currently this requires that each line contains one row of pixel info. Lines starting with '#' will be printed, and not parsed.

optional arguments:
--help displays this message.
there are some others but they aren't documented yet."""

    

if len(sys.argv[0]) > 0: # if being run as a command:
    if len(prog_args) == 0:
        print(USAGE_STRING)
        exit(1)
    for arg in prog_args:
        argSuccess = False
        if arg.startswith("--"):
            if arg == "--help":
                print(HELP_STRING)
                exit(0)
            for keyword_arg_name in keyword_args.keys():
                newValue = get_after_keyword_match(keyword_arg_name, arg)
                if newValue is None:
                    continue
                keyword_args[keyword_arg_name] = newValue
                assert keyword_args[keyword_arg_name] is not None, keyword_arg_name

                argSuccess = True
            if argSuccess == False:
                print("unknown option: {}".format(arg))
                exit(2)
        else:
            nonoption_args.append(arg)
    #for testValue in keyword_args.values():
    #    assert testValue is not None, keyword_args

    assert len(nonoption_args) == 2

    prog_save_filename = nonoption_args[0]
    assert len(prog_save_filename) > 0
    assert ".png" in prog_save_filename

    if nonoption_args[1] == "-":
        run_streaming(prog_save_filename)
        print("run_streaming is over.")
    else:
        prog_data = eval(nonoption_args[1])
        assert len(shape(prog_data)) in {1, 2, 3}

        run_nonstreaming(prog_data, prog_save_filename, "png")
        print("run_nonstreaming is over.")

    print("exiting python.")
    exit(0)
else:
    print("Not in interactive mode.")