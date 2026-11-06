"""Source-constrained stimulus identifiability calculation, not an animal-data fit.

Zhao main Fig3 calibration medians are pooled SONG ELEMENTS, not bird averages.
No sampling uncertainty or population inference is assigned to these medians.
"""
from pathlib import Path
import json
import numpy as np

BASE = Path(__file__).resolve().parents[1]
OUT = BASE / 'outputs'
OUT.mkdir(exist_ok=True)

def ridge_free_affine(x,y):
    b = (y[1]-y[0])/(x[1]-x[0])
    return float(y[0]-b*x[0]),float(b)

def main():
    width=np.array([50.,300.])
    count=np.array([4.,1.])
    total=width*count
    y=np.array([62.3,323.0])
    # Unit-scaled design only: rank is independent of invertible scaling.
    X=np.column_stack([np.ones(2),width/300,count/4,total/300])
    width_coef=ridge_free_affine(width,y)
    dose_coef=ridge_free_affine(total,y)
    count_coef=ridge_free_affine(count,y)
    proportional=float(np.sum(width*y)/np.sum(width*width))
    # Orthogonal crossed design, holding pulse count fixed at four:
    # pulse widths 50 vs 150 ms; onset period 200 vs 400 ms (no overlap).
    # Candidate results are unobserved and serve only experimental design.
    crossed=np.array([[1,w/150,p/400] for w in [50.,150.] for p in [200.,400.]])
    # Width and period factors, centered and equally scaled, are orthogonal.
    factor=np.array([[1,(w-100)/50,(p-300)/100] for w in [50.,150.] for p in [200.,400.]])
    predictions=[]
    for w,p in [(50,200),(50,400),(150,200),(150,400)]:
        predictions.append({'width_ms':w,'onset_period_ms':p,'count':4,
            'width_affine_endpoint_ms':width_coef[0]+width_coef[1]*w,
            'total_light_affine_endpoint_ms':dose_coef[0]+dose_coef[1]*4*w,
            'caution':'affine extrapolation may be physiologically invalid; source sequence model needed'})
    full=np.array([[1,(w-100)/50,(p-300)/100,(n-3),((w-100)/50)*(n-3)]
                   for w in [50.,150.] for p in [200.,400.] for n in [2.,4.]])
    result={
      'status':'initial main-summary interpolation retained as diagnostic ONLY;323ms was later found inconsistent with plotted opto-only median. Use empirical_summary.json for corrected descriptive calibration.',
      'source':'Zhao et al 2019 Fig3; source agent independently verified full main text/figure',
      'source_conditions':[{'width_ms':50,'pulse_count':4,'onset_period_ms':100,'light_on_ms':200,'pooled_element_median_ms':62.3,'birds':7,'elements':25},
                           {'width_ms':300,'pulse_count':1,'onset_period_ms':None,'light_on_ms':300,'pooled_element_median_ms':323.,'birds':4,'elements':7}],
      'original_design_rank':int(np.linalg.matrix_rank(X)),
      'original_design_columns':4,'original_nullity':4-int(np.linalg.matrix_rank(X)),
      'width_affine':dict(zip(['intercept_ms','slope'],width_coef)),
      'total_light_affine':dict(zip(['intercept_ms','slope'],dose_coef)),
      'pulse_count_affine':dict(zip(['intercept_ms','slope_ms_per_pulse'],count_coef)),
      'identity_calibration_abs_error_ms':np.abs(y-width).tolist(),
      'proportional_calibration_slope':proportional,
      'proportional_calibration_abs_error_ms':np.abs(y-proportional*width).tolist(),
      'constant_calibration_mean_ms':float(y.mean()),
      'constant_calibration_abs_error_ms':np.abs(y-y.mean()).tolist(),
      'crossed_width_period_rank':int(np.linalg.matrix_rank(crossed)),
      'crossed_factor_gram':np.einsum('ni,nj->ij',factor,factor).tolist(),
      'crossed_design_limit':'fixed pulse count leaves total dose proportional to width; crossing width/period alone does not separate width from total illumination',
      'full_width_period_count_factorial':{'conditions':8,'rank':int(np.linalg.matrix_rank(full)),
           'columns':['intercept','width','period','count','width_x_count'],
           'gram':np.einsum('ni,nj->ij',full,full).tolist(),
           'meaning':'three-factor design distinguishes linear width, period, count and total-dose components; biological onset mapping/salience confounds still need controls'},
      'counterfactual_design_predictions':predictions,
      'interpretation':'Both main conditions can be interpolated exactly by mutually incompatible stimulus encodings. Zero residual with two affine parameters is not evidence for a representation. Width/period crossing separates those two encodings only; adding pulse count separates linear total-dose components. None identifies downstream evaluative versus motor use.'
    }
    assert result['original_design_rank']==2
    assert result['crossed_width_period_rank']==3
    assert np.allclose(np.einsum('ni,nj->ij',factor,factor),4*np.eye(3))
    (OUT/'intervention_design.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if 'predictions' not in k},indent=2))

if __name__=='__main__':main()
