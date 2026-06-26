# Week 6 Day 2 Validation Summary

## 1. Validation Status

| Item | Status |
|---|---|
| Quantized index built | Completed |
| Run files generated | Completed |
| Metrics computed | Completed |
| Latency recorded | Completed |

## 2. Compression Pipeline Table

| Run Name              | Compression   | Index Built   | Run Output   | Metrics OK   | Latency OK   |   Recall@10 |    MRR@10 |   nDCG@10 |   Index Size MB |   Reconstructed File Size MB |   Compression Ratio vs FP Payload |         MSE |       MAE |   Latency ms/query |   Build Time sec |
|:----------------------|:--------------|:--------------|:-------------|:-------------|:-------------|------------:|----------:|----------:|----------------:|-----------------------------:|----------------------------------:|------------:|----------:|-------------------:|-----------------:|
| w6_N10_M16_none       | nan           | Completed     | Completed    | Completed    | Completed    |    0.266667 | 0.0901323 | 0.124232  |       3.15625   |                      3.16858 |                                 1 | 0           | 0         |            5.2517  |         0        |
| w6_N10_M16_pq         | PQ            | Completed     | Completed    | Completed    | Completed    |    0.266667 | 0.065     | 0.107177  |       0.0123291 |                      3.16858 |                               256 | 0.000472634 | 0.0169268 |            5.41724 |         0.120036 |
| w6_N10_M16_opq_pq     | OPQ+PQ        | Completed     | Completed    | Completed    | Completed    |    0.266667 | 0.0423148 | 0.0883807 |       0.0123291 |                      3.16858 |                               256 | 0.000450466 | 0.0164834 |            5.22281 |        17.0127   |
| w6_N10_M16_ivf_pq     | IVF+PQ        | Completed     | Completed    | Completed    | Completed    |    0.266667 | 0.0656481 | 0.106069  |       0.0123291 |                      3.16858 |                               256 | 0.000439198 | 0.0163011 |            5.4952  |         0.15928  |
| w6_N10_M16_ivf_opq_pq | IVF+OPQ+PQ    | Completed     | Completed    | Completed    | Completed    |    0.266667 | 0.077963  | 0.116206  |       0.0123291 |                      3.16858 |                               256 | 0.00042225  | 0.0159488 |            5.21168 |        16.5048   |

## 3. Build Summary

| run_name              | compression   | input_dir                                      | output_dir                                                  |   num_pages |   total_vectors |   dim |   pq_m |   bits |   nlist |   nprobe |   original_fp_file_size_mb |   original_fp_payload_size_mb |   reconstructed_file_size_mb |   estimated_code_size_mb |   estimated_compression_ratio_vs_fp_payload |   file_ratio_vs_fp_files |         mse |       mae |   build_time_sec | index_built   | reconstruct_mode   |   code_size_bytes_per_vector |   ntotal |   is_trained |
|:----------------------|:--------------|:-----------------------------------------------|:------------------------------------------------------------|------------:|----------------:|------:|-------:|-------:|--------:|---------:|---------------------------:|------------------------------:|-----------------------------:|-------------------------:|--------------------------------------------:|-------------------------:|------------:|----------:|-----------------:|:--------------|:-------------------|-----------------------------:|---------:|-------------:|
| w6_N10_M16_pq         | PQ            | artifacts\embeddings\token_selection\pages_M16 | artifacts\embeddings\joint_compression\pages_M16_pq         |         101 |            1616 |   512 |     16 |      4 |     nan |      nan |                    3.16858 |                       3.15625 |                      3.16858 |                0.0123291 |                                         256 |                        1 | 0.000472634 | 0.0169268 |         0.120036 | True          | nan                |                          nan |      nan |          nan |
| w6_N10_M16_opq_pq     | OPQ+PQ        | artifacts\embeddings\token_selection\pages_M16 | artifacts\embeddings\joint_compression\pages_M16_opq_pq     |         101 |            1616 |   512 |     16 |      4 |     nan |      nan |                    3.16858 |                       3.15625 |                      3.16858 |                0.0123291 |                                         256 |                        1 | 0.000450466 | 0.0164834 |        17.0127   | True          | nan                |                          nan |      nan |          nan |
| w6_N10_M16_ivf_pq     | IVF+PQ        | artifacts\embeddings\token_selection\pages_M16 | artifacts\embeddings\joint_compression\pages_M16_ivf_pq     |         101 |            1616 |   512 |     16 |      4 |       8 |        4 |                    3.16858 |                       3.15625 |                      3.16858 |                0.0123291 |                                         256 |                        1 | 0.000439198 | 0.0163011 |         0.15928  | True          | direct_map         |                            8 |     1616 |            1 |
| w6_N10_M16_ivf_opq_pq | IVF+OPQ+PQ    | artifacts\embeddings\token_selection\pages_M16 | artifacts\embeddings\joint_compression\pages_M16_ivf_opq_pq |         101 |            1616 |   512 |     16 |      4 |       8 |        4 |                    3.16858 |                       3.15625 |                      3.16858 |                0.0123291 |                                         256 |                        1 | 0.00042225  | 0.0159488 |        16.5048   | True          | direct_map         |                            8 |     1616 |            1 |

## 4. Day 2 Conclusion

Week 6 Day 2 validation completed. PQ, OPQ+PQ, IVF+PQ, and IVF+OPQ+PQ pipelines were successfully built and evaluated on the representative setting N=10, M=16. The compressed embeddings produced valid run files, compatible metrics, and latency records. The pipeline is ready for Day 3 batch joint-budget experiments.
