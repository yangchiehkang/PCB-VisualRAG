# Week 7 Day 5 Counterfactual Occlusion Metrics

## Table 12: Occlusion 指标结果

| Metric | Value |
|---|---:|
| Query Count | 10 |
| Valid Query Count | 10 |
| COG Positive Count | 10 |
| COG Positive Rate | 1.0000 |
| Mean Score Original | 0.20149380 |
| Mean Score Gold Mask | 0.00000000 |
| Mean Score Random Mask | 0.20149380 |
| Mean COG_score | 0.20149380 |
| Mean nDCG Original | 1.00000000 |
| Mean nDCG Gold Mask | 0.00000000 |
| Mean nDCG Random Mask | 1.00000000 |
| Mean COG_nDCG | 1.00000000 |
| Status | PASSED |

## Definition

```text
COG_score = Score(Random Mask) - Score(Gold Mask)
COG_nDCG  = nDCG(Random Mask) - nDCG(Gold Mask)
```

## Per-query Results

| Query ID | Score Original | Score Gold Mask | Score Random Mask | COG_score | COG_nDCG | Status |
|---|---:|---:|---:|---:|---:|---|
| q001 | 0.28208059 | 0.00000000 | 0.28208059 | 0.28208059 | 1.00000000 | PASSED |
| q002 | 0.13606575 | 0.00000000 | 0.13606575 | 0.13606575 | 1.00000000 | PASSED |
| q004 | 0.01350269 | 0.00000000 | 0.01350269 | 0.01350269 | 1.00000000 | PASSED |
| q006 | 0.27878006 | 0.00000000 | 0.27878006 | 0.27878006 | 1.00000000 | PASSED |
| q007 | 0.27878006 | 0.00000000 | 0.27878006 | 0.27878006 | 1.00000000 | PASSED |
| q008 | 0.08288908 | 0.00000000 | 0.08288908 | 0.08288908 | 1.00000000 | PASSED |
| q009 | 0.09892566 | 0.00000000 | 0.09892566 | 0.09892566 | 1.00000000 | PASSED |
| q010 | 0.28175521 | 0.00000000 | 0.28175521 | 0.28175521 | 1.00000000 | PASSED |
| q011 | 0.28198810 | 0.00000000 | 0.28198810 | 0.28198810 | 1.00000000 | PASSED |
| q012 | 0.28017085 | 0.00000000 | 0.28017085 | 0.28017085 | 1.00000000 | PASSED |