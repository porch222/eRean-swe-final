export function parseApiError(error) {
  const fieldErrors = {};
  let generalError = '';

  if (!error || typeof error !== 'object') {
    return { fieldErrors, generalError: 'Something went wrong.' };
  }

  Object.entries(error).forEach(([key, value]) => {
    const message = Array.isArray(value) ? value.join(' ') : String(value);
    if (key === 'detail' || key === 'non_field_errors') {
      generalError = message;
    } else {
      fieldErrors[key] = message;
    }
  });

  if (!generalError && Object.keys(fieldErrors).length === 0) {
    generalError = 'Something went wrong.';
  }
  return { fieldErrors, generalError };
}

export function errorMessage(error) {
  const { fieldErrors, generalError } = parseApiError(error);
  if (generalError) return generalError;
  const first = Object.entries(fieldErrors)[0];
  return first ? `${first[0]}: ${first[1]}` : 'Something went wrong.';
}
