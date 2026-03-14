/*
 * LZ4DecompressionPS5.c
 * 
 * PS5 LZ4 Decompression Payload
 * Decompresses .lz4 files to exFAT images for PS5 game installation
 * 
 * Build with PS5 SDK:
 * clang -target x86_64-scei-ps5 -O3 -I/opt/ps5-sdk/include \
 *   -L/opt/ps5-sdk/lib -llz4 -o LZ4DecompressionPS5.elf \
 *   LZ4DecompressionPS5.c
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <fcntl.h>
#include <sys/stat.h>
#include <time.h>
#include <lz4frame.h>

#define CHUNK_SIZE (1024 * 1024)  /* 1MB chunks */
#define PROGRESS_INTERVAL 100     /* Report progress every 100MB */

typedef struct {
    char input_path[1024];
    char output_path[1024];
    int verbose;
} DecompressionOptions;

void print_progress(off_t bytes_processed, off_t total_bytes, time_t start_time) {
    if (total_bytes == 0) return;
    
    double percent = (double)bytes_processed / total_bytes * 100.0;
    time_t elapsed = time(NULL) - start_time;
    double rate = elapsed > 0 ? (double)bytes_processed / (1024.0 * 1024.0 * elapsed) : 0;
    
    printf("\r  %.1f%% | %lld MB | %.1f MB/s", 
           percent, 
           (long long)bytes_processed / (1024 * 1024), 
           rate);
    fflush(stdout);
}

int decompress_lz4(const char *input_file, const char *output_file, int verbose) {
    int ret = 0;
    FILE *f_in = NULL;
    FILE *f_out = NULL;
    void *src_buffer = NULL;
    void *dst_buffer = NULL;
    LZ4F_dctx *dctx = NULL;
    
    printf("\n");
    printf("========================================\n");
    printf("LZ4 Decompression (PS5)\n");
    printf("========================================\n");
    printf("Input:  %s\n", input_file);
    printf("Output: %s\n", output_file);
    printf("========================================\n\n");
    
    /* Get input file size */
    struct stat st;
    if (stat(input_file, &st) != 0) {
        fprintf(stderr, "ERROR: Cannot stat input file: %s\n", input_file);
        return 1;
    }
    off_t file_size = st.st_size;
    
    /* Open files */
    f_in = fopen(input_file, "rb");
    if (!f_in) {
        fprintf(stderr, "ERROR: Cannot open input file: %s\n", input_file);
        return 1;
    }
    
    f_out = fopen(output_file, "wb");
    if (!f_out) {
        fprintf(stderr, "ERROR: Cannot open output file: %s\n", output_file);
        fclose(f_in);
        return 1;
    }
    
    /* Allocate buffers */
    src_buffer = malloc(CHUNK_SIZE);
    dst_buffer = malloc(CHUNK_SIZE * 2);
    if (!src_buffer || !dst_buffer) {
        fprintf(stderr, "ERROR: Memory allocation failed\n");
        ret = 1;
        goto cleanup;
    }
    
    /* Create decompression context */
    LZ4F_errorCode_t err = LZ4F_createDecompressionContext(&dctx, LZ4F_VERSION);
    if (LZ4F_isError(err)) {
        fprintf(stderr, "ERROR: LZ4F_createDecompressionContext failed: %s\n", 
                LZ4F_getErrorName(err));
        ret = 1;
        goto cleanup;
    }
    
    /* Decompress */
    time_t start_time = time(NULL);
    off_t bytes_read = 0;
    off_t bytes_written = 0;
    int chunk_count = 0;
    
    printf("Decompressing...\n");
    
    while (!feof(f_in)) {
        /* Read compressed chunk */
        size_t src_size = fread(src_buffer, 1, CHUNK_SIZE, f_in);
        if (src_size == 0) break;
        
        /* Decompress */
        size_t src_pos = 0;
        while (src_pos < src_size) {
            size_t dst_capacity = CHUNK_SIZE * 2;
            size_t decompressed = LZ4F_decompress(
                dctx,
                dst_buffer,
                &dst_capacity,
                (uint8_t*)src_buffer + src_pos,
                &src_size,
                NULL
            );
            
            if (LZ4F_isError(decompressed)) {
                fprintf(stderr, "\nERROR: Decompression failed: %s\n", 
                        LZ4F_getErrorName(decompressed));
                ret = 1;
                goto cleanup;
            }
            
            /* Write decompressed data */
            if (dst_capacity > 0) {
                size_t written = fwrite(dst_buffer, 1, dst_capacity, f_out);
                if (written != dst_capacity) {
                    fprintf(stderr, "\nERROR: Write failed\n");
                    ret = 1;
                    goto cleanup;
                }
                bytes_written += written;
            }
            
            src_pos += src_size;
            src_size = 0;
        }
        
        bytes_read += src_size;
        chunk_count++;
        
        /* Progress update */
        if (chunk_count % PROGRESS_INTERVAL == 0) {
            print_progress(bytes_written, file_size, start_time);
        }
    }
    
    time_t elapsed = time(NULL) - start_time;
    printf("\n\n========================================\n");
    printf("Decompression Complete!\n");
    printf("========================================\n");
    printf("Output Size: %lld bytes\n", (long long)bytes_written);
    printf("Time:        %ld seconds\n", elapsed);
    if (elapsed > 0) {
        printf("Speed:       %.1f MB/s\n", 
               (double)bytes_written / (1024.0 * 1024.0 * elapsed));
    }
    printf("========================================\n\n");
    
cleanup:
    if (dctx) LZ4F_freeDecompressionContext(dctx);
    if (src_buffer) free(src_buffer);
    if (dst_buffer) free(dst_buffer);
    if (f_in) fclose(f_in);
    if (f_out) fclose(f_out);
    
    return ret;
}

int main(int argc, char *argv[]) {
    if (argc < 3) {
        fprintf(stderr, "Usage: %s <input.lz4> <output>\n", argv[0]);
        fprintf(stderr, "  Decompresses LZ4 file to output\n");
        return 1;
    }
    
    return decompress_lz4(argv[1], argv[2], argc > 4 && strcmp(argv[4], "-v") == 0);
}
