# Implemented recurrence, comparator and target

29 October2026. Methods appendix to [the manuscript](manuscript.md). This describes the frozen implementation and the added postvalidation diagnostic; it changes no model, protocol, outcome or gate.

## Choice policy and recurrent learning rule

Let $s_t=\mathrm{contrastRight}_t-\mathrm{contrastLeft}_t$ and

$$z_t=\frac{\tanh(5s_t)}{\tanh(5)},\qquad x_t=(\max(z_t,0),\min(z_t,0),1)^\top.$$

For responding trials, $p_t=P(\mathrm{right})=\sigma(w_t^\top x_t)$. Native ALF choice coding is $c_t=-1$ for right, $+1$ for left and $0$ for omission. Define $y_t=\mathbf1(c_t<0)$, $r_t=\mathbf1(\mathrm{feedbackType}_t>0)$, and $d_t$ as the session-start indicator. The coefficient vector has three components; recurrent memory has32.

The implemented order is prediction, choice/feedback, then update:

$$u_t=[w_t,z_t,1,d_t,y_t,r_t,\mathbf1(z_t>0)],$$
$$h_{t+1}=\operatorname{GRU}_{32}(u_t,h_t),$$
$$w_{t+1}=w_t+\kappa\odot\left[W_3\operatorname{ReLU}\left(W_2\operatorname{ReLU}(W_1h_{t+1}+b_1)+b_2\right)+b_3\right].$$

Both hidden layers have32 units and the output has three components. Effective saved update scales are $(.08456734,.04597805,.14873186)$. Standard GRU gates use separate input and recurrent affine terms; the pinned implementation and independent recurrence audit retain their exact gate ordering. Both $w$ and $h$ are unchanged on omissions. Primary session boundaries do not reset or multiply these states; $d_t$ enters the updater. The future-only.8 diagnostic multiplies both states at a future session boundary and otherwise retains the primary prescription.

Only $w_0$ is fitted to the1,000-trial prefix. Memory starts at zero; prefix recurrence produces the forecast-start coefficient and memory states. The fitted objective is negative responding-trial prefix log likelihood plus $.25\|w_0\|^2$, with coefficient bounds $[-8,12],[-8,12],[-6,6]$ and initialization from a static fit to the first200 prefix trials. No independent hidden-state parameter or future learning-rate path is fitted.

For autonomous forecasts, a rank-at-most-three Gaussian uncertainty calculation in $w_0$ uses prefix Fisher information plus prior precision.5 and propagates the same perturbations through the prefix Jacobians into both coefficient and memory endpoints. The largest endpoint coefficient-covariance eigenvalue is capped at4 by a common perturbation scale; memory is clipped to $[-1,1]$. The original512-particle forecasts include these correlated initial-state draws. Exact seeds, hashes, checkpoint and optimizer settings remain in the campaign freezes/model metadata. The saved recurrent checkpoint is epoch975, seed557, from the fixed1,000-epoch development ceiling.

The later actual-history diagnostic starts from the saved central endpoint rather than this particle distribution. It receives actual stimuli, predicts before assimilating each observed response/feedback, and computes expected accuracy analytically. It is not a controlled information-only ablation against the autonomous mixture or a posterior recalibration using new data.

## Empirical exposure/growth comparator

Growth is a development-donor forecast, not a linear regression on trial number. On the last500 target-prefix trials, fit a ridge-logistic policy with ridge1 to responding choices and estimate omission probability $o=(n_{\rm omit}+.5)/(500+1)$. Denote the coefficient fit and inverse-Hessian covariance by $\hat v$ and $\hat\Sigma$. The four-dimensional matching feature is $(\hat v,\operatorname{logit}o)$.

For each development donor, the bank stores this same prefix feature, and, in every available future500-trial bin, the separately fitted coefficient change from that donor's prefix, $\Delta v_{jb}$, and omission-logit change $\Delta\ell_{jb}$. Rank donors by squared distance in the four matching features after division by fixed scales $(1.5,1.5,1.5,2)$. Sample uniformly among the nearest15 donors, excluding the forecast animal.

Each particle draws $v_*\sim\mathcal N(\hat v,\hat\Sigma)$, $o_*\sim\operatorname{Beta}(n_{\rm omit}+.5,n_{\rm response}+.5)$ and a donor. In future bin$b$,

$$v_b=v_*+\Delta v_{jb},\qquad o_b=\sigma(\operatorname{logit}o_*+\Delta\ell_{jb}).$$

A donor lacking that future bin is replaced by a sampled donor among the nearest15 valid at that horizon. The growth coefficients follow exposure-indexed donor changes; they do not assimilate the forecast animal's future observations. Its simulated choices nevertheless interact with the adaptive trainer. The frozen donor-based omission process is shared with the neural forecasts. No forecast animal's future is used to construct its donor bank or match.

The population-study persistence arm instead uses the full prefix's fixed policy/covariance, with the frozen prior. Its shared omission process remains distinct from its static response policy. The original study's candidate-specific initialization and uncertainty configurations remain separately specified in its protocol; changing these would define another forecast recipe.

## Population estimand and information distinction

For animal$i$ in future500-opportunity bin$b$, let $N_{ib,L}$ and $N_{ib,R}$ count exact100% stimuli on each side. Omissions remain in these denominators and are failures. The equal-side correct share is

$$A_{ib}=\tfrac12\left(\frac{C_{ib,L}}{N_{ib,L}}+\frac{C_{ib,R}}{N_{ib,R}}\right).$$

Population means average animals equally. Mean-curve error averages the six absolute differences between observed cohort means and mean predicted cohort shares. Individual equal-side MAE takes the absolute error within each animal/bin before averaging; side-specific MAE takes absolute errors before averaging the two sides. These targets are different summaries.

Autonomous predictions average the saved particle summaries under their generated stimulus/choice histories. The actual-history diagnostic evaluates $(1-o_t)p_{\rm correct,t}$ on the observed exact100% trials and averages within the observed side cells. Its $o_t$ is the mean from the unchanged512-particle prefix omission recipe. Thus actual stimulus occurrence and adaptive history, initial-state averaging and response-sampling treatment all differ. The matched-cohort result establishes an operational tracking/forecast distinction, without isolating its causal source.

## Authoritative implementation references

- [Policy and baseline construction](../../campaigns/learning_rule_transport_2026-10-28/code/baselines.py).
- [Recurrent sequence and prefix calibration](../../campaigns/learning_rule_transport_2026-10-28/code/rnn_learning.py).
- [Joint prefix uncertainty and autonomous chronology](../../campaigns/learning_rule_transport_2026-10-28/code/rnn_rollout.py).
- [Population implementation and exact100% summaries](../../campaigns/population_learning_transport_2026-10-28/code/campaign.py).
- [Capped postvalidation diagnostic](../../experiments/matched_history_diagnostic_2026-10-29/run.py).

These descriptions are for scientific transparency. Frozen bytes, forecasts and historical exposure ledgers remain authoritative; the appendix is not a new validation or claim that the source paper used every adaptation above.
