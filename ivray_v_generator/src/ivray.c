/******************************************************************************
           DO WHAT THE FUCK YOU WANT TO PUBLIC LICENSE
                   Version 2, December 2004

Copyright (C) 2024

Everyone is permitted to copy and distribute verbatim or modified
copies of this license document, and changing it is allowed as long
as the name is changed.

           DO WHAT THE FUCK YOU WANT TO PUBLIC LICENSE
  TERMS AND CONDITIONS FOR COPYING, DISTRIBUTION AND MODIFICATION

 0. You just DO WHAT THE FUCK YOU WANT TO.
******************************************************************************/

#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include <ivray.h>

typedef struct {
        uint8_t magic[4];
        uint32_t frame_count;
        float brightness;
        float speed;
} __attribute__((packed)) ivray_header_t;

ivray_t * ivray_new(uint32_t frame_count)
{
        ivray_t *table;

        table = calloc(1, sizeof(ivray_t));
        if (table == NULL) {
                return NULL;
        }

        table->frames = calloc(frame_count, sizeof(ivray_frame_t));
        if (table->frames == NULL) {
                free(table);
                return NULL;
        }

        table->frame_count = frame_count;
        table->brightness = 1.0f;
        table->speed = 1.0f;

        return table;
}

void ivray_free(ivray_t *table)
{
        uint32_t index;

        if (table == NULL) {
                return;
        }

        for (index = 0; index < table->frame_count; index++) {
                free(table->frames[index].vectors);
        }

        free(table->frames);
        free(table);
}

int ivray_record_frame(ivray_t *table, uint32_t frame_index, const int *delta_x,
                       const int *delta_y, uint32_t vector_count)
{
        ivray_frame_t *frame;
        uint32_t vector_index;

        if (table == NULL || frame_index >= table->frame_count) {
                return -1;
        }

        frame = &table->frames[frame_index];

        free(frame->vectors);

        if (vector_count == 0) {
                frame->vector_count = 0;
                frame->vectors = NULL;
                return 0;
        }

        frame->vectors = malloc(sizeof(int16_t) * vector_count * 2);
        if (frame->vectors == NULL) {
                frame->vector_count = 0;
                return -1;
        }

        for (vector_index = 0; vector_index < vector_count; vector_index++) {
                frame->vectors[vector_index * 2] = (int16_t)delta_x[vector_index];
                frame->vectors[vector_index * 2 + 1] = (int16_t)delta_y[vector_index];
        }

        frame->vector_count = vector_count;

        return 0;
}

int ivray_save(const ivray_t *table, const char *path)
{
        ivray_header_t header;
        uint32_t frame_index;
        FILE *fp;

        if (table == NULL || path == NULL) {
                return -1;
        }

        fp = fopen(path, "wb");
        if (fp == NULL) {
                perror("Cannot open ivray file");
                return -1;
        }

        memcpy(header.magic, "IVRY", sizeof(header.magic));
        header.frame_count = table->frame_count;
        header.brightness = table->brightness;
        header.speed = table->speed;

        if (fwrite(&header, sizeof(header), 1, fp) != 1) {
                fclose(fp);
                return -1;
        }

        for (frame_index = 0; frame_index < table->frame_count; frame_index++) {
                const ivray_frame_t *frame = &table->frames[frame_index];
                uint32_t vector_count = frame->vector_count;

                if (fwrite(&vector_count, sizeof(vector_count), 1, fp) != 1) {
                        fclose(fp);
                        return -1;
                }

                if (vector_count > 0) {
                        size_t written = fwrite(frame->vectors, sizeof(int16_t) * 2,
                                                vector_count, fp);
                        if (written != vector_count) {
                                fclose(fp);
                                return -1;
                        }
                }
        }

        if (fclose(fp) != 0) {
                return -1;
        }

        return 0;
}
