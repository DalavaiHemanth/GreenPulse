import pickle
import numpy as np

def predict_overuse(features, return_hint=False):
	"""
	features: list or np.array of input features for the model
	Returns: 'normal', 'warning', or 'critical'
	"""
	with open('ml_model/model.pkl', 'rb') as f:
		model = pickle.load(f)
	pred = model.predict([features])[0]
	# Map model output to alert status
	if pred == 0:
		status = 'normal'
		message = 'All good! Your usage is within normal range.'
		hint = 'Keep up the good work!'
		threshold = 0 # No threshold for normal
	elif pred == 1:
		status = 'warning'
		message = 'Warning: Your usage is higher than average.'
		hint = 'Consider checking high-wattage appliances.'
		threshold = 5 # Example threshold for warning
	else:
		status = 'critical'
		message = 'Critical: Unusual spike detected! Consider checking appliances.'
		hint = 'Immediately check and turn off unnecessary high-wattage appliances.'
		threshold = 10 # Example threshold for critical

	current_usage = features[-1] if features else 0 # Last daily usage as current usage

	if return_hint:
		return status, message, hint, current_usage, threshold
	else:
		return status, message, current_usage, threshold # This branch is not used by app.py currently

