/// @file roundBuffer.h
///
/// @brief Module implementing round buffer, for any given type of data
///
///

#ifndef ROUNDBUFFER_H
#define ROUNDBUFFER_H

//#DEFINE __AVR__ for MCU targets

#ifdef __cplusplus
extern "C" {
#endif

#include <stdint.h>
#include <stdlib.h>
#include <stdbool.h>

#define BUFFER_OK ((int) 0)
#define BUFFER_ERR_INV_PTR ((int) -1)
#define BUFFER_ERR_NO_MEMORY ((int) -2)
#define BUFFER_GET_ON_EMPTY ((int) -3)
#define BUFFER_IVALID_SIZE ((int) -4)
#define BUFFER_NOT_INITIALIZED ((int) -5)

typedef struct {
    size_t head;
    size_t tail;
    size_t size;
    size_t elementSize;
    void *buffer;
}roundBuff;

/// @brief Checks if buffer is empty
///
/// @param self - ptr to roundBuff struct
/// @return true or false
bool roundBuff_isEmpty(volatile const roundBuff *self);

/// @brief Checks if buffer is full
///
/// @param self - ptr to roundBuff struct
/// @return true or false
bool roundBuff_isFull(volatile const roundBuff *self);

/// @brief Initializes the buffer - sets element size, tail, head, and allocate memory
///
/// @param self - ptr to roundBuff struct
/// @param buffSize - number of elements in the buffer
/// @param elSize - size of the single element
/// @return integer status
int roundBuff_init(volatile roundBuff *self, const size_t buffSize, const size_t elSize);

/// @brief Puts single element in the buffer, alters tail and head
///
/// @param self - ptr to roundBuff struct
/// @param data - data to be put, needs to be of elSize given in init
/// @return integer status
int roundBuff_put(volatile roundBuff *self, const void *data);

/// @brief Gets single element from the buffer, alters tail
///
/// @param self - ptr to roundBuff struct
/// @param data - buffer for single element data, needs to be of elSize given in init
/// @return integer status
int roundBuff_get(volatile roundBuff *self, void *data);

/// @brief Resets the buffer and frees the memory
///
/// @param self - ptr to roundBuff struct
/// @return integer status
int roundBuff_destroy(volatile roundBuff *self);

/// @brief Gets multiple elements from the buffer
///
/// @param self - ptr to roundBuff struct
/// @param data - buffer for received data, needs to be big enough to store them
/// @param count - number of elements to be recovered
/// @return actual number of elements recovered
size_t roundBuff_getMany(volatile roundBuff *self, void *data, const size_t count);

#ifdef __cplusplus
}
#endif
#endif /* ROUNDBUFFER_H */
