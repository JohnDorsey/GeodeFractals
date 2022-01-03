#include <stdio.h>
#include <assert.h>
#include <string.h>
#include <stdlib.h>
#include <stdbool.h>
#include <complex.h>
#include <math.h>
// on all builds before 16 nov 2021, color is decided based on drawR and drawI, and the only effect that can be applied after color is decided is iterslide.
// on probably all builds before 30 dec 2021, the seed point itself is not visited.


// ----- c a n v a s   s e t t i n g s -----------------------
#define WIDTH 512
#define HEIGHT 512
static const int ITERLIMIT=1024; //iterlimit is put in this settings category because it has a big impact on image brightness, so other things here need to be adjusted accordingly.
static const int SUPERSAMPLING=8;
static const int PRINT_INTERVAL=256;
#define DO_CLEAR_ON_OUTPUT 1
#define SWAP_ITER_ORDER 1

static const float seedbias_location_real = 0.0;
static const float seedbias_location_imag = 0.0;
static const float seedbias_balance_real = 0.0;
static const float seedbias_balance_imag = 0.0;



// ----- c o l o r   s e t t i n g s ----------------------
#define LOG_COLORS 0
#define WRAP_COLORS 0
static const float COLOR_POWER=0.25;
static const float COLOR_SCALE=16.0;



// ----- f r a c t a l   s e t t i n g s ---------------------------
//mandelbrot:
#define FRACTAL_FORMULA tmpZr = zr;	tmpZi = zi; zr = tmpZr*tmpZr - tmpZi*tmpZi + cr; zi = 2.0*tmpZr*tmpZi + ci;
//julia:
//#define FRACTAL_FORMULA tmpZr = zr; tmpZi = zi; zr = tmpZr*tmpZr - tmpZi*tmpZi - 0.755; zi = 2.0*tmpZr*tmpZi + 0.15;

#define Z_STARTS_AT_C 0 // setting this to 1 is absolutely necessary for julia set buddhabrot generation.

#define JOINT_BUDDHABROT 0
static const bool INVERT_BUDDHABROT=true;



// ----- d r a w i n g   s e t t i n g s -------------------------

#define DO_MEAN_OF_ZSEQ 0

#define DO_VISIT_LINE_SEGMENT 0
static const int POINTS_PER_LINE_SEGMENT=4096;



// ----- n e c e s s a r y   s e t t i n g s --------------------------------------
#define CHANNEL_COUNT 3
static int globalScreenArr[HEIGHT][WIDTH][CHANNEL_COUNT];
static const int ZERO=0;


















int min(int a, int b) {
	return ((a<b)? a : b);
}

int max(int a, int b) {
	return ((a<b)? b : a);
}

void blank_screen(int (*screenArr)[HEIGHT][WIDTH][CHANNEL_COUNT]) {
	for (int y = 0; y < HEIGHT; y++) {
		for (int x = 0; x < WIDTH; x++) {
			for (int c = 0; c < CHANNEL_COUNT; c++) {
				(*screenArr)[y][x][c] = 0;
			}
		}
	}
}

void draw_test_image(int (*screenArr)[HEIGHT][WIDTH][CHANNEL_COUNT]) {
	int risingPixelsDrawn = 0;
	const int bright = 255; const int dim = 0;
	for (int y = 0; y < HEIGHT; y++) {
		for (int x = 0; x < WIDTH; x++) {
			if ( y == 0 ) {
				(*screenArr)[y][x][2] = ((x%2==0)?bright:dim); // side 1: gaps of 1.
			} else if ( y == HEIGHT - 1 ) {
				(*screenArr)[y][x][2] = ((x%4==0)?bright:dim); // side 3: gaps of 3.
			} else if ( x == 0 ) {
				(*screenArr)[y][x][1] = ((y%5==0)?bright:dim); // side 4: gaps of 4.
			} else if ( x == WIDTH - 1 ) {
				(*screenArr)[y][x][1] = ((y%3==0)?bright:dim); // side 2: gaps of 2.
			} else {
				(*screenArr)[y][x][y%3] = risingPixelsDrawn;
				risingPixelsDrawn++;
			}
		}
	}
}

void print_screen(int (*screenArr)[HEIGHT][WIDTH][CHANNEL_COUNT]) {
	printf("# start of print screen.\n");
	float floatVal;
	int intVal;
	for ( int y = 0; y < HEIGHT; y++ ) {
		printf("[");
		for ( int x = 0; x < WIDTH; x++) {
			printf("(");
			for ( int c = 0; c < CHANNEL_COUNT; c++ ) {
				floatVal = (float) ((*screenArr)[y][x][c]);
				#if LOG_COLORS
					floatVal = logf(floatVal + 1.0);
				#endif
				floatVal = (pow(floatVal, COLOR_POWER) * COLOR_SCALE);
				intVal = (int) floatVal;
				#if WRAP_COLORS
					intVal = intVal % 256;
				#endif
				intVal = max(min(intVal, 255), 0);
				if (c < (CHANNEL_COUNT - 1)) {
					printf("%d,", intVal);
				} else {
					printf("%d", intVal);
				}
			}
			printf("),");
		}
		printf("]\n");
	}
	printf("# end of print screen.\n");
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
		//printf("draw success:");
	} else {
		//printf("draw failure:");
	}
}


void visit_line_segment(int (*screenArr)[HEIGHT][WIDTH][CHANNEL_COUNT], float initialDrawR, float initialDrawI, float finalDrawR, float finalDrawI, float cr, float ci) {
	float drawR;
	float drawI;
	float realSpan = (finalDrawR - initialDrawR);
	float imagSpan = (finalDrawI - initialDrawI);
	float realInc = (realSpan/((float) POINTS_PER_LINE_SEGMENT));
	float imagInc = (imagSpan/((float) POINTS_PER_LINE_SEGMENT));
	for (int iii = 0; iii < POINTS_PER_LINE_SEGMENT; iii++) {
		drawR = initialDrawR + realInc*(((float) iii)+1.0);
		drawI = initialDrawI + imagInc*(((float) iii)+1.0);

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
	
	float zrSum = 0.0; float ziSum = 0.0;
	float drawR = 0.0; float drawI = 0.0;
	
		/* tmpZr = zr*zr - zi*zi; tmpZi = 2.0*zr*zi;	zr = tmpZr + cr; zi = tmpZi + ci; */
	int iterationIndex;
	//int iii;
	//float initialDrawR = 0.0; float finalDrawR = 0.0; float initialDrawI = 0.0; float finalDrawI = 0.0;
	
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
			finalDrawR = drawR; finalDrawI = drawI;
			visit_line_segment(screenArr, initialDrawR, initialDrawI, finalDrawR, finalDrawI, cr, ci);
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

float lerp(float startVal, float endVal, float balance) {
	return (endVal*balance)+(startVal*(1.0-balance));
}

void build_buddhabrot(int supersampling, int (*screenArr)[HEIGHT][WIDTH][CHANNEL_COUNT]) {

	printf("# buddhabrot build started.\n");
	
	int superHeight = HEIGHT * supersampling; int superWidth = WIDTH * supersampling;
	int iterIA; int iterIB;
	
	#if SWAP_ITER_ORDER
		int iterLimA = superHeight; int iterLimB = superWidth;
		int (*x) = &iterIB; int (*y) = &iterIA;
	#else
		int iterLimA = superWidth; int iterLimB = superHeight;
		int (*x) = &iterIA; int (*y) = &iterIB;
	#endif
	
	for ( iterIB = 0; iterIB < iterLimB; iterIB++ ) {
		if ( ((iterIB % PRINT_INTERVAL) == 0) && (iterIB != 0) ) {
			printf("# %d of %d sample %s processed.\n", iterIB, iterLimB, ((SWAP_ITER_ORDER==1)?"columns":"rows"));
			print_screen(screenArr);
			#if DO_CLEAR_ON_OUTPUT
				blank_screen(screenArr);
			#endif
		}
		for ( iterIA = 0; iterIA < iterLimA; iterIA++ ) {
			do_jointbrot_point(
				lerp(from_screen_coord((*x), superWidth), seedbias_location_real, seedbias_balance_real),
				lerp(from_screen_coord((*y), superHeight), seedbias_location_imag, seedbias_balance_imag),
				screenArr
			);
			//printf("(%d,%d) ", x, y);
		}
	}
	printf("# done building buddhabrot. printing screen one more time.\n");
	print_screen(screenArr);
	#if DO_CLEAR_ON_OUTPUT
		blank_screen(screenArr);
	#endif
}



int main(int argc, char **argv) {
	printf("# hello.c running.\n");
	//printf("\n");
	assert(HEIGHT > 10);
	assert(WIDTH > 10);
	assert(to_screen_coord(0.01, 256) > 124);
	assert(to_screen_coord(0.01, 256) < 132);
	
	assert(to_screen_coord(from_screen_coord(177, 256), 256) - 177 < 3);
	//printf("# %f", from_screen_coord(24, 256));
	assert(to_screen_coord(from_screen_coord(24, 256), 256) - 24 < 8);

	//	static int screenArr[HEIGHT][WIDTH];
	memset(globalScreenArr, ZERO, sizeof globalScreenArr);
	printf("# hello.c ready.\n");
	//return 0;
	draw_test_image(&globalScreenArr);
	print_screen(&globalScreenArr);
	blank_screen(&globalScreenArr);
	build_buddhabrot(SUPERSAMPLING, &globalScreenArr);
	//do_mandelbrot(SUPERSAMPLING, &globalScreenArr);
	// return 0;
	printf("STOP");
	return 0;
}