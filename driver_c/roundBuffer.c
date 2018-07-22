#include "roundBuffer.h"
#ifndef __AVR__
#include <string.h>
#else
#include <DMAChannel.h>
#endif // __AVR__

static int roundBuff_reset(volatile roundBuff *self);
static bool isPowerOf_2(const unsigned long value);

static int roundBuff_reset(volatile roundBuff *self){
    if(!self)
        return BUFFER_ERR_INV_PTR;

    self->head = 0;
    self->tail = 0;

    return BUFFER_OK;
}

static bool isPowerOf_2(const unsigned long value){
    return (value != 0) && ((value & (value - 1)) == 0);
}

#ifdef __AVR__
static void memcpy16(uint16_t *dest, const uint16_t *src, size_t count)
{
        DMA_TCD1_SADDR = src;
        DMA_TCD1_SOFF = 2;
        DMA_TCD1_ATTR = DMA_TCD_ATTR_SSIZE(1) | DMA_TCD_ATTR_DSIZE(1);
        DMA_TCD1_NBYTES_MLNO = count;
        DMA_TCD1_SLAST = 0;
        DMA_TCD1_DADDR = dest;
        DMA_TCD1_DOFF = 2;
        DMA_TCD1_CITER_ELINKNO = 1;
        DMA_TCD1_DLASTSGA = 0;
        DMA_TCD1_BITER_ELINKNO = 1;
        DMA_TCD1_CSR = DMA_TCD_CSR_START;
        while (!(DMA_TCD1_CSR & DMA_TCD_CSR_DONE)); // wait ;
}
#endif // __AVR__

int roundBuff_init(volatile roundBuff *self, const size_t buffSize, const size_t elSize){
    if(!isPowerOf_2(buffSize))
        return BUFFER_IVALID_SIZE;
    if(self->buffer){
        free(self->buffer);
    }

    self->size = buffSize;
    self->elementSize = elSize;
    self->buffer = (void*) malloc(buffSize * elSize);

    if(!self->buffer)
        return BUFFER_ERR_NO_MEMORY;

    return roundBuff_reset(self);
}

void roudBuff_incrHead(volatile roundBuff *self){
    self->head = (self->head + 1) & (self->size - 1);
    if(self->head == self->tail)
        self->tail = (self->tail + 1) & (self->size - 1); // thanks to 2^n size
}

int roundBuff_put(volatile roundBuff *self, const void *data){
    if(!self || !data)
        return BUFFER_ERR_INV_PTR;

    if(!self->buffer)
        return BUFFER_NOT_INITIALIZED;

    memcpy(self->buffer + self->head * self->elementSize, data, self->elementSize);
    roudBuff_incrHead(self);

    return BUFFER_OK;
}

int roundBuff_get(volatile roundBuff *self, void *data){
    if(!self || !data)
        return BUFFER_ERR_INV_PTR;

    if(roundBuff_isEmpty(self))
        return BUFFER_GET_ON_EMPTY;

    if(!self->buffer)
        return BUFFER_NOT_INITIALIZED;

    memcpy(data, self->buffer + self->tail * self->elementSize, self->elementSize);
    self->tail = (self->tail + 1) & (self->size - 1);

    return BUFFER_OK;
}

size_t roundBuff_getMany(volatile roundBuff *self, void *data, const size_t count){
    size_t tailToEnd = self->size - self->tail;
    size_t remainder = 0;
    size_t total = count;

    if(count > self->size)
        total = self->size;

    else if(count == 0){
        return 0;
    }

    if(!self || !data)
        return BUFFER_ERR_INV_PTR;
    if(!self->buffer)
        return BUFFER_NOT_INITIALIZED;

    if(total <= tailToEnd){
        memcpy(data, self->buffer + self->tail * self->elementSize, count * self->elementSize);
    }
    else{
        memcpy(data, self->buffer + self->head * self->elementSize, self->elementSize);
        memcpy(data + self->elementSize, self->buffer + self->tail * self->elementSize, tailToEnd * self->elementSize);
        remainder = total - tailToEnd;
        memcpy(data + (tailToEnd + 1) * self->elementSize, self->buffer, remainder * self->elementSize);
    }

    self->tail = (self->tail + total) & (self->size - 1);
    return total;
}

bool roundBuff_isEmpty(volatile const roundBuff *self){
  return self->head == self->tail;
}

bool roundBuff_isFull(volatile const roundBuff *self){
  return ((self->head + 1) & (self->size - 1)) == self->tail;
}

int roundBuff_destroy(volatile roundBuff *self){
    if(self->buffer){
        free(self->buffer);
    }
    roundBuff_reset(self);
    return BUFFER_OK;
}

