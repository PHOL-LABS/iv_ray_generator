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

#ifndef _IVRAY_H_
#define _IVRAY_H_ 1

#include <stddef.h>
#include <stdint.h>

typedef struct {
        uint32_t vector_count;
        int16_t *vectors; /* Stored as [dx0, dy0, dx1, dy1, ...] */
} ivray_frame_t;

typedef struct {
        uint32_t frame_count;
        float brightness;
        float speed;
        ivray_frame_t *frames;
} ivray_t;

ivray_t * ivray_new(uint32_t frame_count);
void ivray_free(ivray_t *table);
int ivray_record_frame(ivray_t *table, uint32_t frame_index, const int *delta_x,
                       const int *delta_y, uint32_t vector_count);
int ivray_save(const ivray_t *table, const char *path);

#endif
