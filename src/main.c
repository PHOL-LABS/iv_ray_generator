/******************************************************************************
           DO WHAT THE FUCK YOU WANT TO PUBLIC LICENSE
                   Version 2, December 2004
 
Copyright (C) 2017-2018 Yeonji <yeonji@ieee.org>

Everyone is permitted to copy and distribute verbatim or modified
copies of this license document, and changing it is allowed as long
as the name is changed.
 
           DO WHAT THE FUCK YOU WANT TO PUBLIC LICENSE
  TERMS AND CONDITIONS FOR COPYING, DISTRIBUTION AND MODIFICATION
 
 0. You just DO WHAT THE FUCK YOU WANT TO.
******************************************************************************/

#include <stdio.h>
#include <stdlib.h>
#include <signal.h>
#include <unistd.h>
#include <getopt.h>
#include <limits.h>

#include <image.h>
#include <image_binary.h>
#include <image_edge_dect.h>
#include <bmp.h>
#include <utils.h>
#include <wave.h>
#include <path.h>

int frame_cnt = 0;
int frame_index = 0;
int frame_w = 0;
int frame_h = 0;
int frame_s = 0;

int g_frame_rate = 24;
int g_sample_rate = 48000;
int g_samples_per_frame = 2000;
const char * g_input_path = "./input.mp4";
const char * g_output_path = "./out.wav";

void show_proc(int signal);
static void print_usage(const char *prog_name);
static int parse_positive_int(const char *value, const char *option_name);
static void update_samples_per_frame(void);

int main(int argc, char *argv[])
{
        extern int frame_cnt;
        extern int frame_index;
        extern int frame_w;
        extern int frame_h;
        extern int frame_s;
        char path[64];
        image_t * img;
        wave_t * wav;
        struct sigaction sa;
        int opt;


        while ((opt = getopt(argc, argv, "hi:o:f:r:")) != -1) {
                switch (opt) {
                case 'i':
                        g_input_path = optarg;
                        break;
                case 'o':
                        g_output_path = optarg;
                        break;
                case 'f':
                        g_frame_rate = parse_positive_int(optarg, "frame rate");
                        break;
                case 'r':
                        g_sample_rate = parse_positive_int(optarg, "sample rate");
                        break;
                case 'h':
                        print_usage(argv[0]);
                        return 0;
                default:
                        print_usage(argv[0]);
                        return 1;
                }
        }

        if (optind < argc) {
                g_input_path = argv[optind];
        }

        if (g_frame_rate <= 0) {
                fprintf(stderr, "Frame rate must be greater than zero.\n");
                return 1;
        }

        if (g_sample_rate <= 0) {
                fprintf(stderr, "Sample rate must be greater than zero.\n");
                return 1;
        }

        if (g_sample_rate < g_frame_rate) {
                fprintf(stderr, "Sample rate must be greater than or equal to frame rate.\n");
                return 1;
        }

        update_samples_per_frame();

        create_tmp_dir();

        fprintf(stderr,
                "Configuration: input=%s output=%s frame_rate=%d sample_rate=%d samples_per_frame=%d\n",
                g_input_path, g_output_path, g_frame_rate, g_sample_rate, g_samples_per_frame);

        transform_video(g_input_path, g_frame_rate, g_sample_rate);

        frame_cnt = get_frame_cnt();

        fprintf(stderr, "Do Processing Workflow On Each Frame.\n");

	sa.sa_handler = &show_proc;
	sa.sa_flags = SA_RESTART;
	sigaction(SIGALRM, &sa, NULL);
	alarm(3);

        wav = wave_new(2, g_sample_rate, g_samples_per_frame * frame_cnt);

	for (frame_index = 1; frame_index <= frame_cnt; frame_index++) {
		
		sprintf(path, "./tmp/frames/v-%05d.bmp", frame_index);

		img = bmp_read(path);

		if (frame_w == 0) {
			frame_w = img->width;
			frame_h = img->height;
			frame_s = 3 * frame_w * frame_h * 4;
		}

		image_binary(img);

		image_edge_dect(img);

		image_binary(img);

		// sprintf(path, "./tmp/frames_proc/v-%05d.bmp", frame_index);

		// bmp_save(img, path);

                gen_path(img, wav, frame_index - 1);

		image_free(img);
		
	}

	raise(SIGALRM);

	fprintf(stderr, "\nProcess end.\n");

	alarm(0);

	fprintf(stderr, "\nSaving.\n");

        wave_save(wav, g_output_path);

	wave_free(wav);

	fprintf(stderr, "\nCleaning.\n");

	remove_tmp_dir();

	return 0;
}

void show_proc(int signal)
{
        extern int frame_cnt;
        extern int frame_index;
        extern int frame_s;

	static int priv_index = 0;
	static int time_s = 0;
	static int time_m = 0;
	static int time_h = 0;

	float fps;
	float kbps;
	float speed;

	fps = (frame_index - priv_index) / 3.0;
	kbps = (fps * frame_s)/1000.0;
	priv_index = frame_index;
	speed = (float)fps / (float)24;
	time_s += 3;

	if (time_s == 60) {
		time_s = 0;
		time_m ++;
	}

	if (time_m == 60) {
		time_m = 0;
		time_h ++;
	}

	fprintf(stderr, "\rframe= %d fps= %.1f time=%02d:%02d:%02ds bitrate=%.1fkbits/s speed=%.2fx SIG=%d",\
		frame_index, fps, time_h, time_m, time_s, kbps, speed, signal);
	fflush(stderr);

	alarm(3);
}

static void print_usage(const char *prog_name)
{
        fprintf(stderr,
                "Usage: %s [-i input.mp4] [-o out.wav] [-f frame_rate] [-r sample_rate] [input.mp4]\n",
                prog_name);
        fprintf(stderr, "\nOptions:\n");
        fprintf(stderr, "  -i PATH        Path to the input video file (default: ./input.mp4).\n");
        fprintf(stderr, "  -o PATH        Path to the output WAV file (default: ./out.wav).\n");
        fprintf(stderr, "  -f NUMBER      Video frame rate to extract (default: 24).\n");
        fprintf(stderr, "  -r NUMBER      Audio sample rate for output (default: 48000).\n");
        fprintf(stderr, "  -h             Show this help message.\n");
}

static int parse_positive_int(const char *value, const char *option_name)
{
        char *endptr;
        long parsed;

        parsed = strtol(value, &endptr, 10);
        if (*value == '\0' || *endptr != '\0') {
                fprintf(stderr, "Invalid %s: %s\n", option_name, value);
                exit(EXIT_FAILURE);
        }

        if (parsed <= 0 || parsed > INT_MAX) {
                fprintf(stderr, "%s must be between 1 and %d.\n", option_name, INT_MAX);
                exit(EXIT_FAILURE);
        }

        return (int)parsed;
}

static void update_samples_per_frame(void)
{
        double samples = (double)g_sample_rate / (double)g_frame_rate;

        g_samples_per_frame = (int)(samples + 0.5);

        if (g_samples_per_frame <= 0) {
                g_samples_per_frame = 1;
        }
}
