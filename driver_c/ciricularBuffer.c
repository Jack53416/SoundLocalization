/*
 * ciricularBuffer.c
 *
 *  Created on: 13.07.2018
 *      Author: Jacek
 */
#include "ciricularBuffer.h"

static int ciricularBuff16_reset(volatile ciricularBuff16_t *self);
static bool isPowerOf_2(const unsigned long value);

static int ciricularBuff16_reset(volatile ciricularBuff16_t *self){
	if(!self)
		return BUFFER_ERR_INV_PTR;

	self->head = 0;
	self->tail = 0;

	return BUFFER_OK;
}

static bool isPowerOf_2(const unsigned long value){
    return (value != 0) && ((value & (value - 1)) == 0);
}


int ciricularBuffer16_init(volatile ciricularBuff16_t *self, const size_t size){
    if(!isPowerOf_2(size))
        return BUFFER_IVALID_SIZE;
    self->size = size;
	self->buffer = (uint16_t*) malloc(size * sizeof(uint16_t));
	if(!self->buffer)
		return BUFFER_ERR_NO_MEMORY;

	return ciricularBuff16_reset(self);
}

int ciricularBuff16_put(volatile ciricularBuff16_t *self, const uint16_t data){
	if(!self)
		return BUFFER_ERR_INV_PTR;

	self->buffer[self->head] = data;
	self->head = (self->head + 1) & (self->size - 1);
	if(self->head == self->tail)
		self->tail = (self->tail + 1) & (self->size - 1); // thanks to 2^n size

	return BUFFER_OK;
}

int ciricularBuff16_get(volatile ciricularBuff16_t *self, uint16_t *data){
	if(!self || !data)
		return BUFFER_ERR_INV_PTR;

	if(ciriularBuff_isEmpty(self))
		return BUFFER_GET_ON_EMPTY;

	*data = self->buffer[self->tail];
	self->tail = (self->tail + 1) & (self->size - 1);

	return BUFFER_OK;
}

bool ciriularBuff_isEmpty(volatile const ciricularBuff16_t *self){
	return self->head == self->tail;
}

bool ciricularBuff_isFull(volatile const ciricularBuff16_t *self){
	return ((self->head + 1) & (self->size - 1)) == self->tail;
}

int ciricularBuff16_destroy(volatile ciricularBuff16_t *self){
    if(self->buffer){
        free(self->buffer);
    }
    ciricularBuff16_reset(self);
    return BUFFER_OK;
}
