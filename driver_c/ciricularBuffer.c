/*
 * ciricularBuffer.c
 *
 *  Created on: 13.07.2018
 *      Author: Jacek
 */
#include "ciricularBuffer.h"

static int ciricularBuff16_reset(ciricularBuff16_t *self);

static int ciricularBuff16_reset(ciricularBuff16_t *self){
	if(!self)
		return BUFFER_ERR_INV_PTR;

	self->head = 0;
	self->tail = 0;

	return BUFFER_OK;
}


int ciricularBuffer16_init(ciricularBuff16_t *self, size_t size){
	self->buffer = (uint16_t*) malloc(size * sizeof(uint16_t));
	if(!self->buffer)
		return BUFFER_ERR_NO_MEMORY;

	return ciricularBuff16_reset(self);
}

int ciricularBuff16_put(ciricularBuff16_t *self, uint16_t data){
	if(!self)
		return BUFFER_ERR_INV_PTR;

	self->buffer[self->head] = data;
	self->head = (self->head + 1) % self->size;
	if(self->head == self->tail)
		self->tail = (self->tail + 1) % self->size;

	return BUFFER_OK;
}

int ciricularBuff16_get(ciricularBuff16_t *self, uint16_t *data){
	if(!self || !data)
		return BUFFER_ERR_INV_PTR;

	if(ciriularBuff_isEmpty(self))
		return BUFFER_GET_ON_EMPTY;

	*data = self->buffer[self->tail];
	self->tail = (self->tail + 1) % self->size;

	return BUFFER_OK;
}

bool ciriularBuff_isEmpty(ciricularBuff16_t *self){
	return self->head == self->tail;
}

bool ciricularBuff_isFull(ciricularBuff16_t *self){
	return ((self->head + 1) % self->size) == self->tail;
}
