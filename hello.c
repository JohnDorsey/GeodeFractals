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
#define WIDTH 4096
#define HEIGHT 4096
static const int ITERLIMIT=4096; //iterlimit is put in the canvas settings category because it has such a big impact on image brightness and other things here need to be adjusted accordingly.
static const int SUPERSAMPLING=8;
static const int PRINT_INTERVAL=4096;

static const float seedbias_location_real = -0.75;
static const float seedbias_location_imag = 0.0;
static const float seedbias_balance_real = (2047.0/2048.0);
static const float seedbias_balance_imag = 0.75;



// ----- g e n e r a t i o n   s e t t i n g s ---------------------------
//mandelbrot:
#define FRACTAL_FORMULA tmpZr = zr;	tmpZi = zi; zr = tmpZr*tmpZr - tmpZi*tmpZi + cr; zi = 2.0*tmpZr*tmpZi + ci;
//julia:
//#define FRACTAL_FORMULA tmpZr = zr; tmpZi = zi; zr = tmpZr*tmpZr - tmpZi*tmpZi - 0.755; zi = 2.0*tmpZr*tmpZi + 0.15;

#define Z_STARTS_AT_C 1 //absolutely necessary for julia set buddhabrot generation.

#define JOINT_BUDDHABROT 0
static const bool INVERT_BUDDHABROT=false;



// ----- d r a w i n g   s e t t i n g s -------------------------
#define DO_MEAN_OF_ZSEQ 0
static const int ITERSLIDE_REAL=0;
static const int ITERSLIDE_IMAG=0;
//static const int POINTS_PER_LINE_SEGMENT=4096;


//        ___ ___ ___ ___ ___ ___ ___ ___ ___ ___ ___ ___ ___ ___
// ----- | c | o | l | o | r |   | s | e | t | t | i | n | g | s | ------------
//        -------------------------------------------------------

#define LOG_COLORS 0
#define WRAP_COLORS 0
static const float COLOR_POWER=0.75;
static const float COLOR_SCALE=0.125;




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

void print_screen(int (*screenArr)[HEIGHT][WIDTH][CHANNEL_COUNT]) {
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
	/* printf("[");
	for ( int hackx = 0; hackx < WIDTH; hackx++ ) {
		printf("254,");
	}
	printf("]\n");
	*/
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
		
		//initialDrawR = drawR; initialDrawI = drawI;
		#if DO_MEAN_OF_ZSEQ
			zrSum += zr; ziSum += zi;
			drawR = zrSum/(ii+1.0); drawI = ziSum/(ii+1.0);
		#else
			drawR = zr; drawI = zi;
		#endif
		//finalDrawR = drawR; finalDrawI = drawI;
		//assert(drawR==zr);

		drawX = to_screen_coord(drawR, WIDTH) + (iterationIndex * ITERSLIDE_REAL);
		drawY = to_screen_coord(drawI, HEIGHT) + (iterationIndex * ITERSLIDE_IMAG);
		
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
		
		//(*screenArr)[iterationIndex % HEIGHT][iterationIndex % WIDTH][2] += 1;
		//printf("%f %f %d %d %d %d\n",drawR,drawI,drawX,drawY,WIDTH,HEIGHT);
		
	}
	return;
}



		/* tmpZr = zr*zr - zi*zi; tmpZi = 2.0*zr*zi;	zr = tmpZr + cr; zi = tmpZi + ci; */
/*
if ( ii == 0 ) { continue; }
		for (iii = 0; iii < POINTS_PER_LINE_SEGMENT; iii++) {
			drawR = initialDrawR + ((finalDrawR - initialDrawR)/((float) POINTS_PER_LINE_SEGMENT))*(((float) iii)+1.0);
			drawI = initialDrawI + ((finalDrawI - initialDrawI)/((float) POINTS_PER_LINE_SEGMENT))*(((float) iii)+1.0);
			
			...drawX drawY

			..mark screenArr.
		}
*/

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
	int superHeight = HEIGHT*supersampling;
	int superWidth = WIDTH*supersampling;
	printf("# buddhabrot build started.\n");
	for ( int y = 0; y < superHeight; y++ ) {
		if ( ((y % PRINT_INTERVAL) == 0) && (y != 0) ) {
			printf("# %d of %d rows processed.\n", y, superHeight);
			print_screen(screenArr);
		}
		for ( int x = 0; x < superWidth; x++) {
			do_jointbrot_point(
				lerp(from_screen_coord(x, superWidth), seedbias_location_real, seedbias_balance_real),
				lerp(from_screen_coord(y, superHeight), seedbias_location_imag, seedbias_balance_imag),
				screenArr
			);
			//printf("(%d,%d) ", x, y);
		}
	}
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
	build_buddhabrot(SUPERSAMPLING, &globalScreenArr);
	//do_mandelbrot(SUPERSAMPLING, &globalScreenArr);
	// return 0;
	print_screen(&globalScreenArr);
	printf("STOP");
	return 0;
}