---
title: Training-Time Action Conditioning for Efficient Real-Time Chunking
authors: Kevin Black, Allen Z. Ren, Michael Equi, Sergey Levine
year: 2025
source: https://arxiv.org/abs/2512.05964
---

## Opening

This is Training-Time Action Conditioning for Efficient Real-Time Chunking, by Kevin Black, Allen Ren, Michael Equi and Sergey Levine at Physical Intelligence, released as a preprint in December 2025. It is a short methods paper, six pages including code, and it is a direct follow-up to the same group's real-time chunking paper from earlier that year. If you have not heard that one, the first few minutes here will catch you up.

## The problem

Large robot policies, the vision-language-action models with billions of parameters, cannot produce a new command at every control step. They take tens to hundreds of milliseconds per call, and the robot wants a command every twenty. The established fix is action chunking: predict a block of future actions per call, and play them back while the next block is computed. Done naively, that leaves either pauses at chunk boundaries or jerks when a new chunk starts from a different plan than the old one.

Real-time chunking, or RTC, solved the jerk problem at inference time. While the current chunk plays, the next one is generated in the background. By the time it is ready, its first few actions have already been executed from the old chunk, so those are frozen, and the flow model is steered to generate the rest consistently with them, using a guidance technique from image inpainting. It worked well. But the steering has a cost. Each denoising step needs a backward pass through the network to compute the guidance, which increased model inference time by about a quarter in the original paper. For a method whose entire purpose is to cope with latency, adding latency is awkward.

There is a second, subtler problem the authors report here. The inference-time guidance relies on a local linear approximation of the network. As the frozen prefix grows longer, meaning as inference delay grows, the guidance has to work harder to keep the rest of the chunk consistent, and it starts to fall short. So the original method is weakest exactly where it is needed most.

## The idea in one breath

Do the conditioning at training time instead. During training, pretend there is an inference delay: take a ground-truth action chunk, hand the model the first few actions as a clean, known prefix, and train it to denoise only the remainder. At inference, feed in the real prefix, the actions that have already been committed, and let the model generate the rest directly. No guidance, no backward pass, no extra latency. It slots into the existing real-time chunking runtime as a drop-in replacement for the generation step, and it is a few lines of code.

## Where it sits

The parent method is inference-time real-time chunking, which this paper keeps as the runtime framework and only replaces the generation step of. The comparison to it is the whole paper.

Other approaches to the same tension exist. Hierarchical designs like Gemini Robotics and GR00T split the model into a slow planner and a fast action generator. Smaller architectures like MiniVLA and SmolVLA make the whole model cheap enough to run at the edge. The authors call these orthogonal: they change the architecture and training recipe, whereas this method changes neither.

SmolVLA also ships an asynchronous execution scheme, but it does not address the discontinuity between chunks. Two concurrent papers do. One adds a lightweight correction head. The other, VLASH, conditions on a single future action. This paper conditions on the full prefix of future actions, which is the more complete version of that idea.

## How it works

First, the vocabulary. A chunk is a sequence of actions the model predicts from one observation. The execution horizon is how many of those actions the robot runs before the next chunk takes over. The inference delay is how many control steps pass between requesting a chunk and receiving it. If a chunk is requested at step t, it arrives at step t plus the delay, so its first delay-many actions cannot be executed by the new chunk; they will already have been executed from the previous chunk. Those actions, taken from the previous chunk and overlapping the new one, are the action prefix. For that to work, the delay must be no larger than the chunk length minus the execution horizon, which is the same constraint the original method has.

The policy is trained with flow matching, the standard recipe for these models: mix a real action chunk with noise at a random mixing level, and train the network to predict the direction from noise back toward the clean chunk. At inference, start from pure noise and integrate that direction over a few steps.

The training-time trick is three small changes to that recipe.

Change one is architectural but trivial. The network takes the noise level as a conditioning input, and normally one noise level applies to the whole chunk. The change is to let each action position in the chunk have its own noise level. In a diffusion transformer, the noise level enters through per-block scale, shift and gate parameters, so allowing them to differ per token is a reshape, not a new module. The number of learnable parameters does not change.

Change two is the conditioning. For each training example, sample a delay. Take the first delay-many actions of the ground-truth chunk and feed them in clean, with their noise level set to one, which in this convention means fully denoised. The remaining actions, the postfix, get the usual random noise level and the usual noise. So the model sees a clean prefix and a noisy postfix, and the per-token noise level tells it where the boundary is. That is how the model learns what the delay is; the delay is not passed in as a separate number.

Change three is the loss. Compute the flow matching loss only on the postfix positions and mask out the prefix. The model is never asked to reconstruct the prefix, only to use it.

At inference, the sampler mirrors this. Start from noise. At every denoising step, overwrite the prefix positions with the committed actions and set their noise level to one, run the network, take the step, repeat. The output postfix is the new chunk beyond the prefix. Because this function takes a prefix and a delay and returns a postfix, it has exactly the interface of the generation step in the original runtime, so everything else, the background thread, the delay estimation, the chunk swap, stays as it was.

One practical detail. The real delay is not known ahead of time and varies, so the delay is sampled randomly during training. In the real-robot experiments it is uniform from zero to ten steps, which covers up to two hundred milliseconds at fifty hertz. In simulation they used a distribution weighted toward small delays, because they found large delays need less supervision.

What this gives up relative to the original is soft masking. The original method used not only the executed prefix but all of the overlap with the previous chunk, with exponentially decaying weights, as a soft guide. The training-time version conditions on a hard prefix only. The authors are explicit that this is less flexible.

The whole thing is given as about forty lines of JAX at the end of the paper, with the changed lines highlighted.

## Experiments

Two settings, both inherited from the original paper.

Simulation uses the same twelve dynamic Kinetix tasks: two-dimensional physics with force control, where inference delay cannot be hidden by holding position. Chunk length is eight and the policy is a small MLP-Mixer. The baselines, naive asynchronous and inference-time real-time chunking, share one checkpoint trained normally for thirty-two epochs. The training-time version resumes that run at epoch twenty-four and fine-tunes for eight epochs with prefix conditioning, so all methods get the same training compute. Delays from zero to four are tested, each point over two thousand and forty-eight rollouts with confidence intervals.

The real-world setting uses the group's pi zero point six model on two tasks from their pi zero point six star paper: building a cardboard box, and making espresso, which includes grinding, tamping, extracting and pouring. Two checkpoints are fine-tuned from the base model for eight thousand gradient steps at batch size five hundred and twelve, one normal, one with prefix conditioning. Inference runs on a remote H100 with five denoising steps. Baselines are synchronous execution and inference-time real-time chunking. Metrics are success rate and episode duration, with error bars.

What is not tested. The base model was not pre-trained with prefix conditioning; it was only fine-tuned with it, and the paper shows that works but does not test whether pre-training with it would do better. The delay distribution used in training is stated but not varied, so there is no study of what happens when the real delay falls outside it. No comparison is made to the concurrent methods, VLASH or the correction-head approach. The number of real-world trials is not stated in the text. And the simulated comparison spends the same total compute on every method, which is fair, but the authors note that separate checkpoints per delay would likely do better and were not trained.

## Results

In simulation, training-time real-time chunking beats the inference-time version at delays of two and above, and the gap widens with delay. At delay four the original method has fallen to roughly the sixty percent solve rate range while the training-time version is around seventy. At delays zero and one the training-time version is very slightly worse, which the authors attribute to it spending a little less supervision on the first actions of each chunk. Naive asynchronous execution is far below both at every delay.

On the real robot, the two real-time chunking variants are statistically indistinguishable on both success rate and duration, and both are clearly faster than synchronous execution, which visibly pauses between chunks. The training-time version does this with lower end-to-end latency, about one hundred and eight milliseconds against one hundred and thirty-five, because it skips the guidance backward passes. The abstract's phrase is performance and speed parity at lower cost.

## Conclusion and downsides

This is a small paper with a clear claim and it supports it. The modification is minimal, the code is there, and on the parent method's own benchmark the training-time version is better at the delays that matter and the same on the real tasks, for less compute at inference. The authors also address the practical question of whether you need to retrain from scratch, and show that fine-tuning a normal checkpoint is enough.

The downsides, some stated and some not.

First, flexibility. The authors say it plainly: the training-time version only supports a hard prefix. The original method could also use the rest of the overlapping chunk as a soft guide, and in the original paper that soft masking was shown to matter, especially at small delays. The slight loss at delays zero and one here may be that effect showing up. There is no attempt to recover soft masking at training time, which seems like the obvious next step.

Second, the delay distribution is now a training choice. You have to decide, before training, what delays the deployed system will see. Too narrow and the model is out of distribution when the network hiccups; too wide and supervision is spread thin. The original method adapted to whatever delay it measured. The authors list this as a limitation and give no guidance beyond their two settings.

Third, the real-world result is parity, not improvement. The abstract says improved performance, but the figure and the text say the two variants perform similarly within error bars. The genuine gain in the real world is the latency reduction and simplicity, and that is a fine result, but the summary sentence oversells it.

Fourth, the evaluation is narrow. Two real tasks, one robot, one base model, trial counts not stated, and the simulated results are on a benchmark the same group built for the previous paper.

Fifth, the compute accounting is slightly asymmetric in a way that cuts both directions. Fine-tuning from epoch twenty-four means the conditioned model has seen fewer clean training examples, which the authors flag; but the baseline checkpoint also got no chance to adapt, and neither did any per-delay specialists.

The open problem the authors name is combining the two: getting the soft, flexible conditioning of the inference-time method without its cost. A natural direction is to condition at training time on a soft prefix as well, and nothing in the recipe prevents trying it.

## Recap

The problem was that the original real-time chunking method kept robot motion smooth across chunk boundaries by steering generation with a gradient at inference time, which added latency and weakened as delays grew. The approach is to move that conditioning into training by simulating inference delay. It works by giving the model a clean action prefix with per-position noise levels set to fully denoised, training the loss only on the rest of the chunk, and at inference simply feeding in the committed actions as the prefix; three small code changes and no architectural additions. In simulation it beats the original at delays of two steps or more, and on two real manipulation tasks it matches the original's success and speed at lower latency, with both well ahead of synchronous execution. The main downside is that it only supports a hard prefix, giving up the soft masking the original used, and the range of delays has to be chosen before training. Read the full paper if you already run real-time chunking; the forty lines of code on the last page are the whole method, and the six-page read is shorter than this audiobook.
