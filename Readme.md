# Monitoring the Russo-Ukrainian War Through Media

## About
This repository is a reproduction package for Resonant Journalism in the Russo-Ukrainian War: A Topic Modeling Approach to Key-Point Detection, the thesis for my BSc in Economics (Universidade de Brasília - Brazil)

This study sheds light on the potential of unstructured data for the detection of major happenings in global events. We detect key points of the Russo-Ukrainian War using topic modeling on a newly curated, large-scale dataset of news stories and investigate whether the differences in topic distributions can highlight unique trendsetting potentials in reporting across major news outlets.

#### LDA sheds light on major events throughout the corpus:
![](reports/figures/topic_series/Full_topic_count.svg)

#### Persistent Homology helps us find peak dates:
![](reports/figures/peak_detection/peak_detection_topic_9.svg)
![](reports/figures/peak_detection/peak_detection_topic_61.svg)
![](reports/figures/topic_series/Filtered_topic_count.svg)

#### Kullback-Leibler Divergence allows us to probe for a bias towards innovation in reporting:
![](reports/figures/2dhist/All_RvN_10.svg)
![](reports/figures/2dhist/All_RvN_1000.svg)
![](reports/figures/source_compass/Source_compass.svg)

## In this repo:
### Working scrapers for 11 news outlets:
- ABC, AP, CBS, CNN, DailyMail, Express, Fox, Guardian, Mirror, NY Times, Reuters

### Topic Analysis
- (Barron et al. 2018) Implementation of latent Dirichlet allocation (LDA)
- KLD-Based measures of Novelty, Resonance and Transience

### Plotting notebooks
