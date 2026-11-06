"""Pin and call-graph audit of original release; NOT student learning."""
import ast
import hashlib
import json
import resource
import time
from pathlib import Path

start = time.monotonic()
root = Path(__file__).resolve().parent
expected = {
    'addition_rnn_model.py': 'c3f313303379eb0725c2c64580ee736a577374b0',
    'addition_rnn_teacher.py': 'a9cf303da4ca70e66f2639934e5334eb9ed262bd',
    'addition_rnn_curriculum.py': 'd06ef30e52395bf754bd58fbdce2ed0431046a65',
    'readme.txt': '59e35534ed9c1a1cef87f08043c066c693f19df4',
}
pins = {}
for name, wanted in expected.items():
    payload = (root/'source'/name).read_bytes()
    sha = hashlib.sha1(b'blob '+str(len(payload)).encode()+b'\0'+payload).hexdigest()
    pins[name] = dict(bytes=len(payload), git_blob_sha1=sha, expected=wanted,
                      sha256=hashlib.sha256(payload).hexdigest(), matches=(sha == wanted))
    assert sha == wanted, pins[name]

model_ast = ast.parse((root/'source'/'addition_rnn_model.py').read_text())
teacher_ast = ast.parse((root/'source'/'addition_rnn_teacher.py').read_text())
classes = {n.name:n for n in model_ast.body if isinstance(n, ast.ClassDef)}
def method(cls, name):
    return next(n for n in classes[cls].body if isinstance(n, ast.FunctionDef) and n.name == name)
def called_attributes(node):
    return [n.func.attr for n in ast.walk(node) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)]
step = method('AdditionRNNEnvironment', 'step')
epoch = method('AdditionRNNModel', 'train_epoch')
scorer = method('AdditionRNNModel', 'accuracy_per_length')
assert called_attributes(step).count('train_epoch') == 1
assert called_attributes(step).count('accuracy_per_length') == 1
fit = next(n for n in ast.walk(epoch) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == 'fit')
validation = next(k.value for k in fit.keywords if k.arg == 'validation_data')
assert isinstance(validation, ast.IfExp) and isinstance(validation.body, ast.Tuple)
assert [x.id for x in validation.body.elts] == ['val_X','val_y']
assert called_attributes(scorer).count('predict') == 1
teachers = {}
for cls in teacher_ast.body:
    if isinstance(cls, ast.ClassDef):
        teach = next((n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == 'teach'), None)
        if teach is not None:
            teachers[cls.name] = sum(isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                                   and n.func.attr == 'step' for n in ast.walk(teach))
assert len(teachers) == 5 and all(v == 1 for v in teachers.values())
out = dict(status='SOURCE_PIN_CALL_GRAPH_ONLY_NOT_STUDENT_LEARNING', commit='ec41eea6aa45f68c183b839a3279db4c66857705',
           pins=pins, teacher_step_call_sites=teachers,
           default_step=dict(training_examples=40960, batch_size=4096, optimizer_updates=10,
                             validation_examples_in_fit=4096, validation_examples_in_predict=4096,
                             total_validation_forward_examples=8192, generated_validation_examples_once=4096,
                             validation_updates=0, new_assessment_labels_per_step=0,
                             scope='Source defaults and nonempty validation; not a measured runtime'),
           elapsed_seconds=time.monotonic()-start, peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
           actual_student_examples=0, actual_student_updates=0)
(root/'SOURCE_AUDIT.json').write_text(json.dumps(out, indent=2)+'\n')
print(json.dumps(out, indent=2))
