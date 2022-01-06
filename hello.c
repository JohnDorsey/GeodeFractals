#include <stdio.h>
#include <assert.h>
#include <string.h>
#include <stdlib.h>
#include <stdbool.h>
#include <complex.h>
#include <math.h>
// on all builds before 16 nov 2021, color is decided based on drawR and drawI, and the only effect that can be applied after color is decided is iterslide.
// on probably all builds before 30 dec 2021, the seed point itself is not visited.

#define P0 printf("ARGUMENT --output+=helloc\n");


// ----- f r a c t a l   s e t t i n g s ---------------------------
#define FRACTAL_FORMULA tmpZr = zr;	tmpZi = zi; zr = tmpZr*tmpZr - tmpZi*tmpZi + cr; zi = 2.0*tmpZr*tmpZi + ci; //mandelbrot
//#define FRACTAL_FORMULA tmpZr = zr; tmpZi = zi; zr = tmpZr*tmpZr - tmpZi*tmpZi - 0.755; zi = 2.0*tmpZr*tmpZi + 0.15; //julia

#define JOINT_BUDDHABROT 0
static const bool INVERT_BUDDHABROT=false;

#define Z_STARTS_AT_C 1 // setting this to 1 is absolutely necessary for julia set buddhabrot generation. Also, it shouldn't be set to zero if line segments are being drawn.

#define P1 printf("ARGUMENT --output+=_%s%s\n", (JOINT_BUDDHABROT?"jbb":(INVERT_BUDDHABROT?"abb":"bb")), (Z_STARTS_AT_C?"_zc":"_z0"));


// ----- d r a w i n g   s e t t i n g s -------------------------

#define DO_MEAN_OF_ZSEQ 0

// #define DO_VISIT_LINE_SEGMENT 0
#define POINTS_PER_LINE_SEGMENT 8192
static const float LINE_SEGMENT_C_BIAS_BALANCE = 1.0;

#define DO_VISIT_LINE_SEGMENT (POINTS_PER_LINE_SEGMENT > 1)
#define P2 if (DO_VISIT_LINE_SEGMENT) { assert (Z_STARTS_AT_C); assert(POINTS_PER_LINE_SEGMENT == HEIGHT); } printf("ARGUMENT --output+=%s\n", (DO_MEAN_OF_ZSEQ?"_meanofzseq":"")); if ( DO_VISIT_LINE_SEGMENT ) { printf("ARGUMENT --output+=_%dptsperseg\n", POINTS_PER_LINE_SEGMENT); }


// ----- c a n v a s   s e t t i n g s -----------------------
#define WIDTH 8192
#define HEIGHT 8192
static const int ITERLIMIT=1048576; //iterlimit is put in this settings category because it has a big impact on image brightness, so other things here need to be adjusted accordingly.
static const int BIDIRECTIONAL_SUPERSAMPLING=1;
static const int PRINT_INTERVAL=256;
#define DO_CLEAR_ON_OUTPUT 0
#define OUTPUT_STRIPE_INTERVAL 1 // potential output images with index n will be _calculated and output_ only if n % (this setting) == 0.
#define SWAP_ITER_ORDER 1

static const float SEEDBIAS_LOCATION_REAL = 0.0;
static const float SEEDBIAS_LOCATION_IMAG = -2.0;
static const float SEEDBIAS_BALANCE_REAL = 0.0;
static const float SEEDBIAS_BALANCE_IMAG = 0.5;

#define P3 assert(OUTPUT_STRIPE_INTERVAL >= 1); if (SWAP_ITER_ORDER) { assert(SEEDBIAS_BALANCE_IMAG != 0.0); }; 
#define P4 printf("ARGUMENT --output+=_%ditr%dbisuper%s%s_interval(%dprnt%dstripe)\n", ITERLIMIT, BIDIRECTIONAL_SUPERSAMPLING, (DO_CLEAR_ON_OUTPUT?"_clearonout":""), (SWAP_ITER_ORDER?"_swapiterorder":""), PRINT_INTERVAL, OUTPUT_STRIPE_INTERVAL); if (SEEDBIAS_BALANCE_REAL != 0.0 || SEEDBIAS_BALANCE_IMAG != 0.0) { printf("ARGUMENT --output+=_seedbias(%fto%fand%fto%fi)\n", SEEDBIAS_BALANCE_REAL, SEEDBIAS_LOCATION_REAL, SEEDBIAS_BALANCE_IMAG, SEEDBIAS_LOCATION_IMAG); }


// ----- c o l o r   s e t t i n g s ----------------------
static const int COLOR_BIT_DEPTH=8;
#define WRAP_COLORS 0
#define LOG_COLORS 0
static const float COLOR_POWER=0.5;
static const float COLOR_SCALE=0.5;

static int COLOR_MAX_VALUE;
#define P5 assert(COLOR_SCALE > 0.001); COLOR_MAX_VALUE=int_pow(2, COLOR_BIT_DEPTH);
#define P6 printf("ARGUMENT --channel-depth=%d\n", COLOR_BIT_DEPTH); printf("ARGUMENT --output+=_color(%s%fpow%fscale%dbit%s).png\n", (LOG_COLORS?"log":""), COLOR_POWER, COLOR_SCALE, COLOR_BIT_DEPTH, (WRAP_COLORS?"wrap":"clamp")); printf("ARGUMENT --output.trimfloats\n"); // file name and assertions.


// ------ o u t p u t   s e t t i n g s ------------
#define OUTPUT_ROW_SUBDIVISION 1 // the number of subdivision sections (1 for whole (unsubdivided) rows).
#define BITCAT_THE_CHANNEL_AXIS 1

#define P7 printf("ARGUMENT --row-subdivision=%d\n", OUTPUT_ROW_SUBDIVISION); printf("ARGUMENT --bitcatted-axes=%s\n", (BITCAT_THE_CHANNEL_AXIS?"c":""));



// ----- n e c e s s a r y   s e t t i n g s --------------------------------------
#define CHANNEL_COUNT 3
static int globalScreenArr[HEIGHT][WIDTH][CHANNEL_COUNT];
static const int ZERO=0;
// #define BUFFER_SIZE 256

// ----- unnecessary settings --------------
#define DEFAULT_PIXEL_BRIGHTNESS 0

















int min(int a, int b) {
	return ((a<b)? a : b);
}

int min_index_2(int a, int b) {
	return ((a<b)? 0 : 1);
}

int min_index_4(int a, int b, int c, int d) {
	return (min_index_2(min(a, b), min(c,d))?(2+min_index_2(c,d)):min_index_2(a,b));
	/*
	0 if a < min(b c d)
	1 if b < min(a c d)
	2 if c < min(a b d)
	3 if d < min(a b c)
	(something < a) * (
		1 if b < c d or b < a c d
		2 if c < d or c < b d or c < a b d
		3 if ? or d < c or d < b c or d < a b c
	)
	*/
}

int max(int a, int b) {
	return ((a<b)? b : a);
}

int int_pow(int a, int b) {
	assert( b >= 0 );
	int result = 1;
	for ( int i = 0; i < b; i++ ) {
		result *= a;
	}
	return result;
}

int positive_modulo(int a, int b) {
    return (a%b + b)%b;
}


float lerp(float startVal, float endVal, float balance) {
	return (endVal*balance)+(startVal*(1.0-balance));
}



void fill_screen(int (*screenArr)[HEIGHT][WIDTH][CHANNEL_COUNT], int fillValue) {
	for (int y = 0; y < HEIGHT; y++) {
		for (int x = 0; x < WIDTH; x++) {
			for (int c = 0; c < CHANNEL_COUNT; c++) {
				(*screenArr)[y][x][c] = fillValue;
			}
		}
	}
}

void blank_screen(int (*screenArr)[HEIGHT][WIDTH][CHANNEL_COUNT]) {
	fill_screen(screenArr, DEFAULT_PIXEL_BRIGHTNESS);
}


bool is_in_far_border(int v, int screenMeasure, int borderSize) {
	assert(v >= 0 && v < screenMeasure);
	return (v >= (screenMeasure - borderSize));
}
bool is_in_border(int v, int screenMeasure, int borderSize) {
	assert(v >= 0 && v < screenMeasure);
	return (v < borderSize || is_in_far_border(v, screenMeasure, borderSize));
}
int nearest_side_index(int x, int y, int width, int height) {
	int xOpp = width - x - 1;
	int yOpp = height - y - 1;
	return min_index_4(y, xOpp, yOpp, x);
}


void draw_test_image(int (*screenArr)[HEIGHT][WIDTH][CHANNEL_COUNT]) {
	int risingPixelsDrawn = 0;
	int integerLimit = 2147483648;
	const int bright = 2147483646;
	// const int mediumBright = int_pow(2, (int)(((float)COLOR_BIT_DEPTH) / COLOR_POWER))-1;
	const int dim = 0;
	int (*currentCell)[CHANNEL_COUNT];
	for (int y = 0; y < HEIGHT; y++) {
		for (int x = 0; x < WIDTH; x++) {
			currentCell = &((*screenArr)[y][x]);
			if (is_in_border(y, HEIGHT, 8) || is_in_border(x, WIDTH, 8)) {
				if ( y == 0 ) {
					(*currentCell)[2] = ((x%2==0)?bright:dim); // side 1: gaps of 1.
				} else if ( y == HEIGHT - 1 ) {
					(*currentCell)[2] = ((x%4==0)?bright:dim); // side 3: gaps of 3.
				} else if ( x == 0 ) {
					(*currentCell)[1] = ((y%5==0)?bright:dim); // side 4: gaps of 4.
				} else if ( x == WIDTH - 1 ) {
					(*currentCell)[1] = ((y%3==0)?bright:dim); // side 2: gaps of 2.
				} else {
					(*currentCell)[y%3] = risingPixelsDrawn;
					risingPixelsDrawn++;
				}
			} else if (is_in_border(y, HEIGHT, 32) || is_in_border(x, WIDTH, 32)) {
				(*currentCell)[0] = (y*x);
				(*currentCell)[1] = (y*y*x*x);
				(*currentCell)[2] = (y*y*y*x*x*x);
			} else if (is_in_border(y, HEIGHT, 128) || is_in_border(x, WIDTH, 129)) {
				(*currentCell)[0] = ((*screenArr)[y-1][x-1][0] + (*screenArr)[y-1][x][0] + (*screenArr)[y-1][x+1][0]);
				(*currentCell)[1] = (((*screenArr)[y-1][x-1][1] + (*screenArr)[y-1][x-1][2]*((y+x)*4>HEIGHT)) * ((*screenArr)[y-1][x][1] + (*screenArr)[y-1][x][2]*((y+WIDTH-x)*3>HEIGHT)) * ((*screenArr)[y-1][x+1][1]+(*screenArr)[y-1][x+1][2]*((y)*2>HEIGHT)));
				(*currentCell)[2] = (
					(*screenArr)[y-1][x-1][2]
					+ (*screenArr)[y-2][x-1+(2*((*screenArr)[y-1][x][0]>(*screenArr)[y-1][x-1][1]))][1]
					+ (*screenArr)[y-2][x-1+(2*((*screenArr)[y-1][x][1]>(*screenArr)[y-1][x-1][2]))][0]
					+ (*screenArr)[y-1][x+1][2]
				);
			} else if (is_in_border(y, HEIGHT, 240) || is_in_border(x, WIDTH, 240)) {
				(*screenArr)[y+1][positive_modulo(x + (*screenArr)[y-1][x][0], WIDTH-512) + 256][0] = (*screenArr)[y-1][x][0] + (*screenArr)[y-1][x][1] + (*screenArr)[y-1][x][2];
				(*screenArr)[y+1][positive_modulo(0 + (*screenArr)[y-1][x][1], WIDTH-512) + 256][1] = (*screenArr)[y-1][x-1][0] + (*screenArr)[y-1][x][1] + (*screenArr)[y-1][x+1][2];
				
				(*screenArr)[max(positive_modulo(x + (*screenArr)[y-1][x][2], HEIGHT-512) + 256, y+1)][positive_modulo(y + (*screenArr)[y-1][x][2], WIDTH-512) + 256][1+(y>x)] = (*screenArr)[y-1][x][0] * (*screenArr)[y-1][x][1] * (*screenArr)[y-1][x][2];
			} else {
				(*currentCell)[0] = 0;
				(*currentCell)[1] = 0;
				(*currentCell)[2] = 0;
			}
		}
	}
	
	int lastTrespassRed = 0;
	int colorStepSize = 123;
	for (int y = 0; y < HEIGHT; y++) {
		for (int x = 0; x < WIDTH; x++) {
			currentCell = &((*screenArr)[y][x]);
			if (is_in_border(y, HEIGHT, 256) || is_in_border(x, WIDTH, 256)) {
				lastTrespassRed = max((*currentCell)[0], lastTrespassRed-16) + colorStepSize;
				y = HEIGHT/2 + positive_modulo(y, 32);
				x = WIDTH/2 + positive_modulo(x, 32);
				(*currentCell)[1] += colorStepSize;
			} else {
				(*currentCell)[2] += colorStepSize;
				(*currentCell)[0] += lastTrespassRed; // (*currentCell)[1] + (*currentCell)[2] + 2;
				x -= 1 + ((*currentCell)[0] % 2) == 0;
				y -= 1 + ((*currentCell)[1]/colorStepSize % 2) == 0;
			}
			if ( (*currentCell)[1] > colorStepSize*1000 || (*currentCell)[2] > colorStepSize*1000 ) {
				goto AfterWanderLoop;
			}
		}
	}
AfterWanderLoop:

	(*screenArr)[1][1][0] = bright; (*screenArr)[1][1][1] = dim; (*screenArr)[1][1][2] = dim;
	(*screenArr)[1][2][0] = dim; (*screenArr)[1][2][1] = bright; (*screenArr)[1][2][2] = dim;
	(*screenArr)[1][3][0] = dim; (*screenArr)[1][3][1] = dim; (*screenArr)[1][3][2] = bright;
}


int process_color_component(int inputValue) {
	
	float floatVal = (float) inputValue;
	
	#if LOG_COLORS
		floatVal = logf(floatVal + 1.0);
	#endif
	
	floatVal = (pow(floatVal, COLOR_POWER) * COLOR_SCALE);
	
	int intVal = (int) floatVal;
	
	#if WRAP_COLORS
		intVal = intVal % COLOR_MAX_VALUE;
	#endif
	
	intVal = max(min(intVal, COLOR_MAX_VALUE-1), 0);
	return intVal;
}


void print_color(int (*color)[CHANNEL_COUNT]) {
	
	#if BITCAT_THE_CHANNEL_AXIS
	
		int intVal = 0;
		for ( int c = 0; c < CHANNEL_COUNT; c++ ) {
			intVal = (intVal * COLOR_MAX_VALUE);
			intVal = intVal + process_color_component((*color)[c]);
		}
		printf("%d,", intVal);
	#else
		printf("(");
		for ( int c = 0; c < CHANNEL_COUNT; c++ ) {
			printf("%d%s", process_color_component((*color)[c]), (c<(CHANNEL_COUNT-1))?",":"");
		}
		printf("),");
	#endif
}


void print_screen(int (*screenArr)[HEIGHT][WIDTH][CHANNEL_COUNT]) {
	printf("# start of print screen.\n");
	int intVal;
	for ( int y = 0; y < HEIGHT; y++ ) {
		//printf("# start of row %d.\n", y);
		printf("[");
		for ( int x = 0; x < WIDTH; x++) {
			#if (OUTPUT_ROW_SUBDIVISION > 1)
				if ( x > 0 && x % (WIDTH / OUTPUT_ROW_SUBDIVISION) == 0) {
					printf("]\n[");
				}
			#endif
			print_color(&((*screenArr)[y][x]));
		}
		printf("]\n");
		//printf("# end of row %d.\n", y);
	}
	printf("# end of print screen.\n");
	for ( int i = 0; i < 128; i++ ) {
		printf("# end of print screen, filler text line %d. This filler text prevents the pipe from stalling.\n", i);
	}
	fflush(stdin);
	return;
}

int to_screen_coord(float v, int screenMeasure) {
	//v = (v+2.0)/4.0;
	// assert(v <= 1);
	// assert(v >= 0);
	//int result = ((int) (((v+2.0)/4.0 ) * ((float) screenMeasure))); // <-- almost works.
	// assert(result >= 0);
	// assert(result < screenMeasure);
	//int result = ((int) (v * ((float) screenMeasure))) % screenMeasure;
	//return 0; //---------------------------------------------------------------------------------------------------------------------------
	
	//assert(HEIGHT > 10);
	//assert(WIDTH > 10);
	/*
	float vShrunk;
	vShrunk = (v+2.0) / 4.0;
	float vLarge;
	assert(screenMeasure > 10);
	vLarge = vShrunk * ((float) screenMeasure);
	int result;
	result = (int) vLarge;
	
	return result;
	*/
	return (int) ((v+2.0) * 0.25 * ((float) screenMeasure)); //0.25 is just the inverse of 4 here.
}

float from_screen_coord(int x, int screenMeasure) {
	//return 0.5;
	/*
	float denom;
	denom = (float) screenMeasure;
	assert(denom > 1.5);
	float vSmall;
	vSmall = ((float) x)/denom;
	return ((float) ((vSmall*4.0)-2.0));
	*/
	return (( ((float) x) / ((float) screenMeasure) * 4.0) - 2.0);
}






int calc_mandelbrot_point(float cr, float ci) {
	#if Z_STARTS_AT_C
		float zr=cr; float zi=ci;
	#else
		float zr=0.0; float zi=0.0;
	#endif
	float tmpZr; float tmpZi;
	//float cr=real; float ci=imag;
	for ( int i = 0; i < ITERLIMIT; i++ ) {
		//tmpZr = zr*zr - zi*zi; tmpZi = 2.0*zr*zi; zr = tmpZr + cr; zi = tmpZi + ci;
		FRACTAL_FORMULA
		if ( (zr*zr + zi*zi) > 16 ) {
			return i;
		}
	}
	return 0;
}



bool jointbrot_point_should_be_skipped(float cr, float ci) {
	/*if ( ! JOINT_BUDDHABROT ) {
		if ( (calc_mandelbrot_point(cr, ci) <= 0) != INVERT_BUDDHABROT ) {
			return true;
		}
	}
	return false;*/
	#if JOINT_BUDDHABROT
		return false;
	#else
		if ( (calc_mandelbrot_point(cr, ci) <= 0) != INVERT_BUDDHABROT ) {
			return true;
		}
		return false;
	#endif
}



void visit_point(int (*screenArr)[HEIGHT][WIDTH][CHANNEL_COUNT], float drawR, float drawI, float cr, float ci) {
	int drawX = to_screen_coord(drawR, WIDTH);
	int drawY = to_screen_coord(drawI, HEIGHT);

	if ( (drawX>=0) && (drawX<WIDTH) && (drawY>=0) && (drawY<HEIGHT) ) {
		//(drawX>=0) && (drawX<WIDTH) && (drawY>=0) && (drawY<HEIGHT)
		//( ! (drawX>=WIDTH || drawX < 0 || drawY>=HEIGHT || drawY < 0) )
		(*screenArr)[drawY][drawX][0] += 1;
		if ( drawR > cr ) { (*screenArr)[drawY][drawX][1] += 1; }
		if ( drawI > ci ) {	(*screenArr)[drawY][drawX][2] += 1;	}
	}
}


void visit_line_segment(int (*screenArr)[HEIGHT][WIDTH][CHANNEL_COUNT], float initialDrawR, float initialDrawI, float finalDrawR, float finalDrawI, float cr, float ci) {
	float drawR;
	float drawI;
	float realSpan = (finalDrawR - initialDrawR);
	float imagSpan = (finalDrawI - initialDrawI);
	float realInc = (realSpan/((float) POINTS_PER_LINE_SEGMENT));
	float imagInc = (imagSpan/((float) POINTS_PER_LINE_SEGMENT));
	for (int iii = 1; iii <= POINTS_PER_LINE_SEGMENT; iii++) {
		drawR = initialDrawR + realInc*iii;
		drawI = initialDrawI + imagInc*iii;

		visit_point(screenArr, drawR, drawI, cr, ci);
	}
}


void do_jointbrot_point(float cr, float ci, int (*screenArr)[HEIGHT][WIDTH][CHANNEL_COUNT]) {

	if (jointbrot_point_should_be_skipped(cr, ci)) { return; }

	//printf("\ncr%f ci%f w%d h%d:",cr,ci,WIDTH,HEIGHT);
	//float cAbsSquared=cr*cr + ci*ci;
	//float zAbsSquared;
	#if Z_STARTS_AT_C
		float zr=cr; float zi=ci;
	#else
		float zr=0.0; float zi=0.0;
	#endif
	float tmpZr; float tmpZi;
	int drawX; int drawY;
	
	float drawR = zr; float drawI = zi;
	
	int iterationIndex;
	
	//optionals:
	float zrSum = 0.0; float ziSum = 0.0;
	float initialDrawR = 0.0; float initialDrawI = 0.0;
	
	for ( iterationIndex = 0; iterationIndex < ITERLIMIT; iterationIndex++ ) {
		//(*screenArr)[iterationIndex % HEIGHT][iterationIndex % WIDTH][0] += 1;
		//printf("iter%d starts zr=%f zi=%f.", iterationIndex, zr, zi);
		FRACTAL_FORMULA
		//printf("now zr=%f zi=%f.",zr,zi);
		if ( (zr*zr + zi*zi) > 16.0 ) {
			return;
		}
		//(*screenArr)[iterationIndex % HEIGHT][iterationIndex % WIDTH][1] += 1;
		
		#if DO_VISIT_LINE_SEGMENT
			initialDrawR = drawR; initialDrawI = drawI;
		#endif
		
		#if DO_MEAN_OF_ZSEQ
			zrSum += zr; ziSum += zi;
			drawR = zrSum/(ii+1.0); drawI = ziSum/(ii+1.0);
		#else
			drawR = zr; drawI = zi;
		#endif
		
		#if DO_VISIT_LINE_SEGMENT
			visit_line_segment(
				screenArr,
				lerp(initialDrawR, cr, LINE_SEGMENT_C_BIAS_BALANCE),
				lerp(initialDrawI, ci, LINE_SEGMENT_C_BIAS_BALANCE),
				drawR, drawI, cr, ci
			);
		#else
			visit_point(screenArr, drawR, drawI, cr, ci);
		#endif
		//(*screenArr)[iterationIndex % HEIGHT][iterationIndex % WIDTH][2] += 1;
		//printf("%f %f %d %d %d %d\n",drawR,drawI,drawX,drawY,WIDTH,HEIGHT);
		
	}
	return;
}



		/* tmpZr = zr*zr - zi*zi; tmpZi = 2.0*zr*zi;	zr = tmpZr + cr; zi = tmpZi + ci; */



/*
//this does not obey lerp rules.
void do_mandelbrot() {
	int val;
	//printf("[");
	for ( int y = 0; y < HEIGHT; y++ ) {
		printf("[");
		for ( int x = 0; x < WIDTH; x++) {
			val = calc_mandelbrot_point(from_screen_coord(x, WIDTH), from_screen_coord(y, HEIGHT));
                        // val = (val)*(LUMABET_LEN-1)/ITERLIMIT;
			val = val * 256 / ITERLIMIT;
			//printf("%c", LUMABET[val]);
			assert(val<256);
			printf("(%d,0,0),", val);
		}
		printf("]\n");
	}
	//printf("]");
	return;
}
*/


void build_buddhabrot(int bidirectional_supersampling, int (*screenArr)[HEIGHT][WIDTH][CHANNEL_COUNT]) {

	printf("# buddhabrot build started.\n");
	
	int superHeight = HEIGHT * bidirectional_supersampling; int superWidth = WIDTH * bidirectional_supersampling;
	int iterIA; int iterIB;
	
	#if SWAP_ITER_ORDER
		int iterLimA = superHeight; int iterLimB = superWidth;
		int (*x) = &iterIB; int (*y) = &iterIA;
	#else
		int iterLimA = superWidth; int iterLimB = superHeight;
		int (*x) = &iterIA; int (*y) = &iterIB;
	#endif
	
	int stripeIndex;
	for ( iterIB = 0; iterIB < iterLimB; iterIB++ ) {
		stripeIndex = iterIB / PRINT_INTERVAL;
		if ( (stripeIndex % OUTPUT_STRIPE_INTERVAL) != 0 ) {
			continue;
		}
		
		for ( iterIA = 0; iterIA < iterLimA; iterIA++ ) {
			do_jointbrot_point(
				lerp(from_screen_coord((*x), superWidth), SEEDBIAS_LOCATION_REAL, SEEDBIAS_BALANCE_REAL),
				lerp(from_screen_coord((*y), superHeight), SEEDBIAS_LOCATION_IMAG, SEEDBIAS_BALANCE_IMAG),
				screenArr
			);
			//printf("(%d,%d) ", x, y);
		}
		
		if ( ((iterIB+1) % PRINT_INTERVAL) == 0 ) { // if this is the last pass through this strip:
			printf("# %d of %d sample %s processed. end of stripe %d.\n", iterIB, iterLimB, (SWAP_ITER_ORDER?"columns":"rows"), stripeIndex);
			print_screen(screenArr);
			#if DO_CLEAR_ON_OUTPUT
				blank_screen(screenArr);
			#endif
		}
		
	}
	printf("# done building buddhabrot.\n");
	/*
	printf("# printing screen one more time...\n");
	print_screen(screenArr);
	#if DO_CLEAR_ON_OUTPUT
		blank_screen(screenArr);
	#endif
	*/
}



int main(int argc, char **argv) {
	assert( 9 / 10 == 0 );
	assert( 5 / 3 == 1);
	//assert(-5 % 3 > 0);
	//assert(-3 % 5 > 0);
	
	// assert(positive_modulo(5, -3) > 0);
	// assert(positive_modulo(3, -5) > 0);
	assert(positive_modulo(-5, 3) > 0);
	assert(positive_modulo(-3, 5) > 0);
	
	// assert(positive_modulo(-5, -3) > 0);
	// assert(positive_modulo(-3, -5) > 0);
	printf("# hello.c running.\n");
	P0
	P1
	P2
	P3
	P4
	P5
	P6
	P7
	printf("# done printing args.\n");
	assert(HEIGHT > 10);
	assert(WIDTH > 10);
	assert(to_screen_coord(0.01, 256) > 124);
	assert(to_screen_coord(0.01, 256) < 132);
	
	assert(to_screen_coord(from_screen_coord(177, 256), 256) - 177 < 3);
	//printf("# %f", from_screen_coord(24, 256));
	assert(to_screen_coord(from_screen_coord(24, 256), 256) - 24 < 8);
	//int color[3]; color[0] = 255; color[1] = 0; color[2];
	//printf("#
	printf("# done with tests.\n");
	printf("# initializing globalScreenArr...\n");

	memset(globalScreenArr, ZERO, sizeof globalScreenArr);
	printf("# blanking out globalScreenArr....\n");
	blank_screen(&globalScreenArr);
	printf("# ready to start.\n");
	
	printf("# drawing test image...\n");
	draw_test_image(&globalScreenArr);
	print_screen(&globalScreenArr);
	blank_screen(&globalScreenArr);
	printf("# done with test image.");
	
	build_buddhabrot(BIDIRECTIONAL_SUPERSAMPLING, &globalScreenArr);
	//do_mandelbrot(SUPERSAMPLING, &globalScreenArr);
	// return 0;
	printf("STOP");
	return 0;
}