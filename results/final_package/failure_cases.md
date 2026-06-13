# Failure Cases

- num_cases: `8`

## Case 1

- run: `paper_instrdialog_router_only_s123`
- segment: `16`
- token_f1: `0.0000`
- lcs_overlap: `0.0000`
- bad_prefix_mismatch: `True`
- routing: `b7` vs oracle `b7` (margin `6.3750`)
- instruction: `In this task, you are given a question. Your task is to generate an answer that is relevant to the question.`
- input_excerpt: `Is it stressful all the time?`

### Gold

Always.

### Prediction

yes, all the time. I feel like I'm constantly on edge. I try to relax, but it's hard when you're in a high-pressure job. I'm a lawyer, you know. I have to be perfect all the time. I'm not sure I can handle it. I'm considering quitting.

## Case 2

- run: `paper_instrdialog_router_only_s123`
- segment: `3`
- token_f1: `0.0000`
- lcs_overlap: `0.0000`
- bad_prefix_mismatch: `True`
- routing: `b7` vs oracle `b7` (margin `6.3203`)
- instruction: `In this task, you are given a question. Your task is to generate an answer that is relevant to the question.`
- input_excerpt: `Are you still living there?`

### Gold

I moved.

### Prediction

I'm still living in the old house.

## Case 3

- run: `paper_instrdialog_router_only_s123`
- segment: `3`
- token_f1: `0.0000`
- lcs_overlap: `0.0000`
- bad_prefix_mismatch: `True`
- routing: `b7` vs oracle `b7` (margin `6.0156`)
- instruction: `In this task, you are given a question. Your task is to generate an answer that is relevant to the question.`
- input_excerpt: `Is it stressful all the time?`

### Gold

Always.

### Prediction

It can be all the time.

## Case 4

- run: `paper_instrdialog_router_only_s123`
- segment: `17`
- token_f1: `0.0000`
- lcs_overlap: `0.0000`
- bad_prefix_mismatch: `True`
- routing: `b7` vs oracle `b7` (margin `5.8906`)
- instruction: `In this task, you are given a question. Your task is to generate an answer that is relevant to the question.`
- input_excerpt: `Is it stressful all the time?`

### Gold

Always.

### Prediction

Yes, it is stressful all the time. I feel like I'm walking around with a weight on my shoulders. I just want to be able to relax and enjoy life. Is that too much to ask?

## Case 5

- run: `paper_instrdialog_router_only_s123`
- segment: `15`
- token_f1: `0.0000`
- lcs_overlap: `0.0000`
- bad_prefix_mismatch: `True`
- routing: `b7` vs oracle `b7` (margin `5.7969`)
- instruction: `In this task, you are given a question. Your task is to generate an answer that is relevant to the question.`
- input_excerpt: `Is it stressful all the time?`

### Gold

Always.

### Prediction

Yes, it is stressful all the time. I feel like I'm walking around with a weight on my shoulders. I just want to be able to relax and enjoy my life. I'm tired of being anxious all the time. I just want to be me again. I just want to be happy again. I just

## Case 6

- run: `paper_instrdialog_router_only_s123`
- segment: `2`
- token_f1: `0.0000`
- lcs_overlap: `0.0000`
- bad_prefix_mismatch: `True`
- routing: `b7` vs oracle `b7` (margin `5.5156`)
- instruction: `In this task, you are given a question. Your task is to generate an answer that is relevant to the question.`
- input_excerpt: `Is it stressful all the time?`

### Gold

Always.

### Prediction

I have a lot of anxiety. I get nervous about things that might go wrong. I try to stay positive but it's hard. I have to remind myself that things will work out. I just need to relax. I need to calm down. I need to breathe. I need to let go. I need to

## Case 7

- run: `paper_instrdialog_router_only_s123`
- segment: `8`
- token_f1: `0.0000`
- lcs_overlap: `0.0000`
- bad_prefix_mismatch: `True`
- routing: `b7` vs oracle `b7` (margin `5.4375`)
- instruction: `In this task, you are given a question. Your task is to generate an answer that is relevant to the question.`
- input_excerpt: `Are you still living there?`

### Gold

I moved.

### Prediction

Yes, I'm still living there. I'm still living there. I'm still living there. I'm still living there. I'm still living there. I'm still living there. I'm still living there. I'm still living there. I'm still living there. I'm still living there. I'm

## Case 8

- run: `paper_instrdialog_router_only_s123`
- segment: `9`
- token_f1: `0.0000`
- lcs_overlap: `0.0000`
- bad_prefix_mismatch: `True`
- routing: `b7` vs oracle `b7` (margin `4.9062`)
- instruction: `In this task, you are given a question. Your task is to generate an answer that is relevant to the question.`
- input_excerpt: `Is it stressful all the time?`

### Gold

Always.

### Prediction

No, it's not all the time. But it can be overwhelming at times. The job requires me to be on call 24/7, which can be tiring. Additionally, the work can be emotionally draining at times. But overall, I enjoy my job and find it rewarding.
