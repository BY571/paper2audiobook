---
title: A Deep Reinforcement Learning Framework for the Financial Portfolio Management Problem
authors: Zhengyao Jiang, Dixing Xu, Jinjun Liang
year: 2017
source: https://arxiv.org/abs/1706.10059
---

## Opening

This is A Deep Reinforcement Learning Framework for the Financial Portfolio Management Problem, by Zhengyao Jiang, Dixing Xu and Jinjun Liang at Xi'an Jiaotong-Liverpool University, released as a preprint in 2017. It is a methods paper with an applied flavour. It proposes a way to train a neural network to directly output portfolio weights, and tests it by back-testing on a cryptocurrency exchange.

## The problem

Portfolio management means continuously deciding how to split a pot of money across a set of assets, with the goal of growing the pot while keeping risk in check. A trading robot does this at fixed intervals. At each step it looks at recent prices and decides the new allocation, then pays fees to move from the old allocation to the new one.

The authors group existing approaches into a few families. Traditional online portfolio selection strategies follow the winner, follow the loser, or match patterns in historical windows. These are built on hand-made financial models, and they only work as well as the model fits the market. Then there are deep learning approaches, but most of them predict future prices and leave the actual trading decision to a separate hand-coded layer. That has two flaws. Prices are very hard to predict, so the whole pipeline lives or dies by prediction accuracy. And because the decision layer is hand-coded, it is awkward to make it care about things like transaction costs.

Reinforcement learning is a natural fit because it learns actions directly from reward. But prior reinforcement learning trading work produced discrete buy, hold, or sell signals for a single asset, which does not generalise to a portfolio. Deep Q-learning, which drove the video game successes, needs a discrete action space, and discretising portfolio weights is both risky and scales badly with the number of assets. Actor-critic methods handle continuous actions but the authors note that training two networks at once is difficult and often unstable.

So the paper wants a fully learned system that outputs continuous portfolio weights, accounts for transaction cost, scales to any number of assets, and can be trained stably without a critic.

## The idea in one breath

Train a single policy network that takes recent price history for every asset plus the current allocation, and directly outputs the new allocation. Because the reward for a chosen allocation can be computed exactly from the price history, you can do gradient ascent on the reward itself, with no critic and no exploration. Three design choices make it work: identical per-asset sub-networks with shared weights, a memory of past allocations so the network learns to avoid fee-heavy churn, and an online mini-batch training scheme that keeps learning while trading.

## Where it sits

The closest prior work is the authors' own earlier paper, which used one integrated convolutional network over all assets at once. The problem they found is that an integrated network learns the identity of each asset and remembers its history. If an asset did badly in the past, the network refuses to invest in it even when it is now clearly rising. This paper fixes that by making the network asset-agnostic.

The other reference point is direct reinforcement by Moody and Saffell, which also optimises trading returns directly and uses a recurrent memory to account for transaction costs. The authors argue that recurrent memory suffers from vanishing gradients and forces training to be sequential, so it cannot be parallelised across a mini-batch. Their portfolio memory is meant to get the same benefit without those costs.

Against the classical online portfolio selection literature, the comparison is head to head on the same data, with a dozen published strategies as baselines. Against deep reinforcement learning more broadly, the paper sidesteps the actor-critic family entirely by exploiting the fact that in back-testing, the environment does not react to your actions.

## How it works

Start with the setup. Time is cut into thirty-minute periods. The portfolio holds twelve things: Bitcoin as the cash, and eleven other coins chosen as the most traded by volume in the thirty days before the experiment starts. The volume ranking is taken from before the test window on purpose, to avoid survivorship bias.

The input to the network at each step is a small block of numbers: for each of the eleven coins, the closing, highest, and lowest price over the last fifty periods, about a day of history. Every price is divided by the coin's latest closing price, so the network sees relative movement rather than absolute price levels. Coins that did not exist yet at some point in the training history get flat, unchanging fake prices, because the authors found that decaying fake prices in their earlier work taught the network to permanently avoid those coins.

Now the network itself, which the authors call an ensemble of identical independent evaluators. The key structural rule is that information never flows between coins until the very last step. Each coin's price history is processed by its own small evaluator, but all evaluators share the same weights. Each evaluator produces a single score for its coin, a vote for how much it expects the coin to grow in the next period. Then the scores for all coins plus a learned bias for cash go through a softmax, which turns them into weights that are positive and sum to one. Those weights are the new portfolio.

They build three versions of the evaluator. A convolutional one, where the convolution kernels have height one so that they only ever look along the time axis of a single coin. A basic recurrent one, which runs a small recurrent network over the fifty-period history of each coin. And a long short-term memory version of the same. In all three, the previous period's portfolio weights are injected as an extra input just before the final scoring step. That is how the network can learn to be reluctant to move money when moving it would cost fees.

The ensemble design has three practical consequences the authors emphasise. Training time grows roughly linearly with the number of coins. Every price window is effectively used eleven times, once per coin, so data is used efficiently. And since the evaluator does not know which coin it is looking at, you can swap coins in and out of the portfolio without retraining.

Next, transaction cost. The paper uses a flat commission of a quarter of a percent on both buying and selling, which is the maximum rate on the exchange. Moving from one allocation to another shrinks the portfolio by a factor that depends on how much has to be bought and sold. That factor cannot be written in closed form because it appears on both sides of its own definition, so the authors solve it iteratively and prove in the appendix that the iteration converges from any starting guess between zero and one. During training they run a fixed number of iterations; during back-testing they iterate until it stops changing.

The reinforcement learning framing is deliberately minimal. The state is the price block plus the previous allocation. The action is the new allocation. The reward for a period is the logarithm of the portfolio's growth in that period, after fees. The total objective is the average of those log returns over the training window, which is just the log of final wealth divided by the number of periods. Dividing by the number of periods makes windows of different lengths comparable so mini-batches can be used.

Here is the important simplification. The authors assume the agent's trades are too small to move the market. Under that assumption, the future prices do not depend on the agent's actions, and the reward of any allocation can be computed exactly from the data. There is no need to estimate a value function and no need to explore, because you can evaluate every possible action on the same slice of history for free. So the policy is deterministic and is trained by plain gradient ascent on the reward, with Adam, on mini-batches. The authors call this full exploitation. Randomness comes only from weight initialisation.

Two more pieces make mini-batch training possible. The first is the portfolio vector memory. It is a stack of allocation vectors, one per period, initialised to uniform weights. When the network is trained on a batch covering some window of periods, it reads the allocation stored for the period just before the window, and after computing its outputs, overwrites the memory entries for the window. As training proceeds the memory converges along with the weights. This means different batches can be trained in parallel without unrolling a recurrent chain through time, and gradients never have to flow back through the memory.

The second is online stochastic batch learning. Markets keep producing new data, so the training set grows forever. After each new period is added, the network is trained on a few mini-batches whose starting points are sampled with a geometrically decaying probability, so recent data is chosen more often than old data. The batches are consecutive windows of fifty periods, and windows that overlap by all but one period are treated as distinct batches. The same scheme is used for pre-training before the test and for continued learning during the test, with thirty online training steps per period.

## Experiments

Everything is on Poloniex, a cryptocurrency exchange, with Bitcoin as the quote currency. There are three back-tests, each about fifty days long: September to October 2016, December 2016 to January 2017, and March to April 2017. Each back-test has its own training set that ends when the back-test begins, covering roughly one and a half to two years of half-hourly data. A separate cross-validation window in mid 2016 was used to pick hyperparameters, and the authors state that it does not overlap the back-tests.

The three ensemble networks are compared against their own earlier integrated convolutional network, three benchmarks, and a dozen classical online portfolio strategies. The benchmarks are best stock, meaning the single coin that did best over the window in hindsight, uniform buy and hold, and uniform constant rebalancing. The classical methods include Anticor, online moving average reversion, passive aggressive mean reversion, robust median reversion, online Newton step, universal portfolios, exponentiated gradient and several others, all run at the same thirty-minute frequency with the same commission.

Metrics are final portfolio value as a multiple of starting value, the Sharpe ratio, and maximum drawdown.

What is not tested. This is one exchange, one asset class, and one period in crypto history. There are no stock, futures or foreign exchange markets. There is no live trading, only back-tests. The back-tests assume zero slippage and zero market impact, so fills always happen at the last price regardless of size. The trading period is fixed at thirty minutes and the portfolio at twelve assets; neither is varied. There is no reporting of variance across training runs or random seeds. And the comparison against other deep reinforcement learning methods is limited to the authors' own previous network; no actor-critic baseline is trained.

## Results

The headline numbers are large. In the first back-test the convolutional ensemble multiplied its money by about thirty in fifty days, the basic recurrent one by about thirteen, and the long short-term memory one by about seven. The best single coin over that window returned about twenty percent, and almost every classical strategy lost money, because a quarter percent fee every thirty minutes eats any small edge. In the second back-test, the worst of the three for the new networks, they still returned between four and eight times, against best stock at about forty percent. In the third, a strongly rising market, the recurrent network made about forty seven times and the convolutional about thirty two, while best stock made about four and a half and robust median reversion, the strongest classical method, about seven.

The three ensembles take the top three positions in final value and Sharpe ratio in all three tests. They do not win on maximum drawdown: their worst peak to trough losses run from about twenty percent to nearly fifty percent, and the constant rebalancing benchmark is safer on that measure. The earlier integrated network from the authors' previous paper lands far behind, at one and a half to four and a half times.

## Conclusion and downsides

The paper's structural contributions are sensible and have aged reasonably well as design ideas. Asset-agnostic evaluators with shared weights, feeding the previous allocation back in so the network learns about fees, and an exact iterative treatment of transaction cost are all things later work has reused. The observation that you can do full exploitation without a critic when the environment is a fixed price history is correct and cleanly explained.

The empirical claims are a different matter, and there are several reasons to be careful.

First, the two assumptions the authors themselves flag, zero slippage and zero market impact, are not minor in this setting. Rebalancing among small-cap altcoins every thirty minutes is exactly where slippage is worst. A strategy that returns thirty times in fifty days on paper is telling you as much about the back-test's fill model as about the strategy.

Second, all three windows fall inside the 2016 to 2017 cryptocurrency boom. The networks beat best stock in hindsight, which is a meaningful bar, but there is no bear market, no sideways market, and no other asset class. The authors acknowledge that the framework has only been tested in one market.

Third, the evaluation is thin. Three windows of fifty days, one training run per network, no confidence intervals, no ablation of the three components. We do not learn how much of the gain comes from the ensemble structure versus the portfolio memory versus online learning. The gap between the long short-term memory version and the basic recurrent version is explained with a speculation about markets repeating themselves, and then, in the same paragraph, with the admission that the same hyperparameters were used for both.

Fourth, the objective is myopic by construction. With a discount of zero the agent maximises each period's log return given the previous allocation and never plans ahead. The authors note this and suggest a critic network as future work, which would reintroduce exactly the actor-critic complexity they set out to avoid.

Fifth, drawdowns of twenty to fifty percent within fifty days would be unacceptable to most real allocators, and the paper does not attempt any risk control beyond what the softmax structure gives for free.

Finally, a note from outside the paper. This work became widely known and was reimplemented many times by practitioners. As far as I am aware, those attempts generally did not reproduce returns of this size on later data, which is consistent with the concerns above rather than with a flaw in the method's logic.

The open problems the paper leaves are real: how to learn market impact from live trading records, how to extend to markets with different microstructure, and how to give the agent a longer horizon without losing training stability.

## Recap

The problem was learning to allocate capital across many assets directly from price data, with transaction costs, without a hand-coded decision layer and without the instability of actor-critic training. The approach is a deterministic policy network that outputs portfolio weights and is trained by gradient ascent on realised log returns, which is possible because back-tested returns can be computed exactly. It works through identical weight-sharing evaluators per asset joined by a softmax, a memory of past allocations that lets the network learn to avoid fee churn, and an online mini-batch scheme that keeps training during trading. In three fifty-day back-tests on a crypto exchange it multiplied capital by between four and forty seven times, far ahead of a dozen classical strategies and the best single coin. The main downside is that these results rest on zero slippage, zero market impact, a single booming market, and three windows with one run each. Read the full paper if you are building a portfolio agent and want the transaction cost derivation and the network layouts; treat the return figures as an upper bound, not an expectation.
