document.addEventListener('DOMContentLoaded', () => {
  const predictBtn = document.getElementById('predictBtn');
  const clearBtn = document.getElementById('clearBtn');
  const inputText = document.getElementById('inputText');
  const resultBadge = document.getElementById('resultBadge');
  const resultText = document.getElementById('resultText');
  const confidenceText = document.getElementById('confidenceText');
  const charCount = document.getElementById('charCount');

  if (inputText && charCount) {
    inputText.addEventListener('input', () => {
      charCount.textContent = `${inputText.value.length} characters`;
    });
  }

  if (predictBtn) {
    predictBtn.addEventListener('click', async () => {
      const text = inputText.value.trim();

      if (!text) {
        resultBadge.textContent = 'No input';
        resultText.textContent = 'Please enter text before predicting.';
        confidenceText.textContent = '';
        return;
      }

      predictBtn.disabled = true;
      predictBtn.textContent = 'Predicting...';

      try {
        const response = await fetch('/api/text-predict', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({ text })
        });

        const data = await response.json();

        resultBadge.textContent = data.prediction;
        resultText.textContent = `Model prediction: ${data.prediction}`;
        confidenceText.textContent = `Confidence: ${Number(data.confidence).toFixed(4)}`;
      } catch (error) {
        resultBadge.textContent = 'Error';
        resultText.textContent = 'Prediction failed. Check server logs.';
        confidenceText.textContent = '';
        console.error(error);
      } finally {
        predictBtn.disabled = false;
        predictBtn.textContent = 'Predict Text';
      }
    });
  }

  if (clearBtn) {
    clearBtn.addEventListener('click', () => {
      inputText.value = '';
      charCount.textContent = '0 characters';
      resultBadge.textContent = 'Waiting for input';
      resultText.textContent = 'No prediction yet. Enter text and click Predict Text.';
      confidenceText.textContent = '';
    });
  }
});