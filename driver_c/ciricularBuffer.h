/*
 * ciricularBuffer.h
 *
 *  Created on: 13.07.2018
 *      Author: Jacek
 */

#ifndef CIRICULARBUFFER_H
#define CIRICULARBUFFER_H

#ifdef __cplusplus
extern "C" {
#endif

#include <stdint.h>
#include <stdlib.h>
#include <stdbool.h>

#define BUFFER_OK 0
#define BUFFER_ERR_INV_PTR -1
#define BUFFER_ERR_NO_MEMORY -2
#define BUFFER_GET_ON_EMPTY -3
#define BUFFER_IVALID_SIZE -4

typedef struct {
	uint16_t *buffer;
	size_t head;
	size_t tail;
	size_t size;

}ciricularBuff16_t;

typedef struct{
	uint32_t *buffer;
	size_t head;
	size_t tail;
	size_t size;
}ciricularBuff32_t;

typedef struct{
	uint64_t *buffer;
	size_t head;
	size_t tail;
	size_t size;
}ciricularBuff64_t;

int ciricularBuffer16_init(volatile ciricularBuff16_t *self, const size_t size);
int ciricularBuff16_put(volatile ciricularBuff16_t *self, const uint16_t data);
int ciricularBuff16_get(volatile ciricularBuff16_t *self, uint16_t *data);
bool ciriularBuff_isEmpty(volatile const ciricularBuff16_t *self);
bool ciricularBuff_isFull(volatile const ciricularBuff16_t *self);
int ciricularBuff16_destroy(volatile ciricularBuff16_t *self);

#ifdef __cplusplus
}
#endif
#endif /* CIRICULARBUFFER_H */
