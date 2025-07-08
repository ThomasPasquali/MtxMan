// main.c
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>

#include "make_graph.h"
#include "graph_generator.h"
#include "user_settings.h"  // Needed to override initiator parameters

int main(int argc, char** argv) {
    if (argc < 4) {
        fprintf(stderr, "Usage: %s <scale> <edge_factor> <output_file.mtx>\n", argv[0]);
        return EXIT_FAILURE;
    }

    int scale = atoi(argv[1]);
    int edge_factor = atoi(argv[2]);
    const char* output_file = argv[3];
    int64_t desired_nedges = (int64_t)edge_factor << scale;
    int64_t nedges;
    packed_edge* edges;
    uint64_t seed1 = 12345, seed2 = 67890;

    /*/ Set custom initiator probabilities (Graph500 standard)
    initiator[0] = 0.57;
    initiator[1] = 0.19;
    initiator[2] = 0.19;
    initiator[3] = 0.05;*/

    // Generate the graph
    make_graph(scale, desired_nedges, seed1, seed2, &nedges, &edges);

    // Determine the number of vertices
    int64_t max_vertex = 0;
    for (int64_t i = 0; i < nedges; ++i) {
        int64_t src = get_v0_from_edge(&edges[i]);
        int64_t dst = get_v1_from_edge(&edges[i]);
        if (src > max_vertex) max_vertex = src;
        if (dst > max_vertex) max_vertex = dst;
    }
    int64_t num_vertices = max_vertex + 1;

    // Write Matrix Market format
    FILE* f = fopen(output_file, "w");
    if (!f) {
        perror("fopen");
        free(edges);
        return EXIT_FAILURE;
    }

    fprintf(f, "%%%%MatrixMarket matrix coordinate pattern general\n");
    fprintf(f, "%% File generated with MtxMan.\n");
    fprintf(f, "%% Scale: %d\n", scale);
    fprintf(f, "%% Edge factor: %d\n", edge_factor);
    fprintf(f, "%ld %ld %ld\n", num_vertices, num_vertices, nedges);
    for (int64_t i = 0; i < nedges; ++i) {
        int64_t src = get_v0_from_edge(&edges[i]) + 1;  // 1-based indexing
        int64_t dst = get_v1_from_edge(&edges[i]) + 1;
        fprintf(f, "%ld %ld\n", src, dst);
    }
    fclose(f);
    free(edges);
    return EXIT_SUCCESS;
}
