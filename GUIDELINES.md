# Audiobook guidelines

You are writing a script that will be read aloud by a text-to-speech voice and listened to
by someone who has not read the paper. They are walking, driving, or cooking. They cannot see
anything. They want to come away knowing what the paper is about, how it works, where it sits
among other work, and whether it is worth reading in full later.

The script is not a summary of the PDF. It is you explaining the paper to a smart colleague
who works in a neighbouring field.

## Length

Aim for 10 to 15 minutes. The voice reads about 150 words per minute, so that is roughly 1500
to 2200 words.
A long or dense paper may justify up to 20 minutes. A short workshop paper may need only 7.
Do not pad. Do not compress the "how it works" or "downsides" sections to hit a number.

## Structure

Use these sections, in this order, as `##` headings. Headings are not spoken; they only add a
pause. Budgets are guidance, not rules.

### 1. Opening (30 to 60 words)
Title, first author or group, venue and year if known. One sentence saying what kind of paper
this is: a new method, an analysis, a benchmark, a theory result.

### 2. The problem (150 to 250 words)
What is unsolved, and why it matters. Give the listener the concrete pain the authors are
reacting to. If the problem needs background to understand, give the background here, briefly.

### 3. The idea in one breath (50 to 100 words)
The core insight in plain words. If the listener remembers one thing, it is this paragraph.

### 4. Where it sits (150 to 250 words)
What the current best approaches do and where they fall short. Then what this paper does
differently. Name the two or three most relevant prior methods by their common names so the
listener can place the paper. Do not list a related work section.

### 5. How it works (350 to 600 words)
The mechanism, told as a story. What are the moving parts, what does each one do, how do they
fit together, and why did the authors make those choices. Explain design decisions and what
they trade off. This is the longest section. No equations, no symbol names, no loss function
notation. If a component is a standard building block, say its name and move on.

### 6. Experiments (150 to 250 words)
What was tested: which tasks, environments, datasets, model sizes, and which baselines. Be
explicit about what was NOT tested, because that is what a listener needs to judge relevance.
For example: "All experiments are on state-based continuous-control tasks in MuJoCo. Nothing
is tested on image observations, discrete actions, or real hardware." Or: "Evaluated on models
up to seven billion parameters, English only."

### 7. Results (80 to 150 words)
Short. Headline outcomes spoken as comparisons: "about twice as sample efficient as the
strongest baseline", "matches the prior best on most tasks and loses on two". Mention if
gains are within noise or if the baselines were retuned. Detailed numbers belong on paper.

### 8. Conclusion and downsides (250 to 400 words)
This can be long. Limitations the authors admit, and ones they do not. Assumptions that may
not hold elsewhere. Compute cost, data needs, engineering complexity, sensitivity to
hyperparameters. Open problems the paper leaves. Your honest assessment of whether the idea
is likely to transfer beyond the tested setting.

### 9. Recap (80 to 120 words)
Five short statements, one each: the problem, the approach, how it works, how it performs,
and the main downside. Then one sentence on who should read the full paper.

## Writing for the ear

- Write as you would speak. Short sentences. One idea per sentence.
- No equations, no variable names, no Greek letters, no loss notation. Describe what a
  quantity means, not how it is written. "The gap between predicted and observed reward"
  instead of "delta".
- Expand every acronym the first time. "Proximal policy optimization, or PPO" and then "PPO".
- Say numbers in a way that can be heard: "about a third faster", "twelve percent", "roughly
  two hundred thousand samples". Round aggressively. No decimals beyond one place.
- No references to things the listener cannot see: no "Figure 3", no "Table 2", no "Section 4",
  no "as shown above", no citation numbers.
- No bullet lists in the script. Lists are spoken as sentences.
- Mention author names at most once. Say "the authors" afterwards.
- Do not read the abstract. Do not read section titles from the paper.
- Avoid filler like "in this paper we", "it is worth noting", "interestingly".
- When you are unsure of a claim, say so: "the paper suggests", "the authors argue".
- Keep the tone neutral and informed. You are not selling the paper.

## Script file format

```
---
title: Paper title
authors: First Author, Second Author
year: 2026
source: https://arxiv.org/abs/XXXX.XXXXX
---

## Opening

Paragraph text.

## The problem

Paragraph text. Another paragraph after a blank line.
```

Each blank-line-separated paragraph is one synthesis unit. Keep paragraphs under about
120 words so that the voice has natural breaks.

## Self-check before synthesizing

Go through the script and answer each with yes or no. Fix every no.

1. Is every section present, in order?
2. Is the "how it works" section the longest, and does it explain why, not just what?
3. Does the experiments section say what was not tested?
4. Does the downsides section contain at least one limitation the authors did not state themselves?
5. Are there zero equations, symbols, variable names, figure or table references?
6. Is every acronym expanded on first use?
7. Are all numbers rounded and spoken as comparisons?
8. Could a listener who has never seen the paper follow every paragraph?
9. Is the word count between about 1500 and 2200, or justified if outside?
10. Does the recap stand alone as a one-minute version of the whole thing?
