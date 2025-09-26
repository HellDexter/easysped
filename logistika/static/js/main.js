document.addEventListener('DOMContentLoaded', function() {
    // Live datetime display
    const datetimeElement = document.getElementById('live-datetime');
    if (datetimeElement) {
        function updateDateTime() {
            const now = new Date();
            const date = now.toLocaleDateString('cs-CZ', { day: '2-digit', month: '2-digit', year: 'numeric' });
            const time = now.toLocaleTimeString('cs-CZ', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
            datetimeElement.textContent = `${date} ${time}`;
        }
        updateDateTime();
        setInterval(updateDateTime, 1000);
    }

    // Clickable table rows
    const rows = document.querySelectorAll('tr[data-href]');
    rows.forEach(row => {
        row.addEventListener('click', () => {
            window.location.href = row.dataset.href;
        });
    });

    // Calculator logic
    const calculator = document.querySelector('.calculator');
    if (calculator) {
        const screen = calculator.querySelector('.calculator-screen');
        const keys = calculator.querySelector('.calculator-keys');
        let displayValue = '0';
        let firstOperand = null;
        let operator = null;
        let waitingForSecondOperand = false;

        function updateScreen() {
            screen.value = displayValue;
        }

        updateScreen();

        keys.addEventListener('click', (event) => {
            const { target } = event;
            const { value } = target;

            if (!target.matches('button')) {
                return;
            }

            // Odebrání zvýraznění z ostatních kláves
            Array.from(keys.children).forEach(k => k.classList.remove('is-depressed'));

            switch (value) {
                case '%':
                    handlePercent();
                    break;
                case '+':
                case '-':
                case '*':
                case '/':
                case '=':
                    handleOperator(value, target);
                    break;
                case '.':
                    inputDecimal(value);
                    break;
                case 'all-clear':
                    resetCalculator();
                    break;
                default:
                    if (Number.isInteger(parseInt(value))) {
                        inputDigit(value);
                    }
            }
            updateScreen();
        });

        function inputDigit(digit) {
            if (waitingForSecondOperand) {
                displayValue = digit;
                waitingForSecondOperand = false;
            } else {
                displayValue = displayValue === '0' ? digit : displayValue + digit;
            }
        }

        function inputDecimal(dot) {
            if (waitingForSecondOperand) {
                displayValue = '0.';
                waitingForSecondOperand = false;
                return;
            }
            if (!displayValue.includes(dot)) {
                displayValue += dot;
            }
        }

        function handlePercent() {
            const currentValue = parseFloat(displayValue);
            if (firstOperand === null || !operator) {
                // Case: A % -> A / 100
                displayValue = (currentValue / 100).toString();
            } else {
                // Case: A + B % or A * B %
                const percentValue = (firstOperand * currentValue) / 100;
                if (operator === '+' || operator === '-') {
                    // A + (A * B / 100)
                    const result = performCalculation[operator](firstOperand, percentValue);
                    displayValue = `${parseFloat(result.toFixed(7))}`;
                    firstOperand = result;
                } else if (operator === '*' || operator === '/') {
                    // A * (B / 100)
                    displayValue = percentValue.toString();
                }
            }
            waitingForSecondOperand = true;
        }

        function handleOperator(nextOperator, target) {
            const inputValue = parseFloat(displayValue);

            target.classList.add('is-depressed'); // Zvýrazníme stisknutý operátor

            if (operator && waitingForSecondOperand) {
                operator = nextOperator;
                return;
            }

            if (firstOperand === null) {
                firstOperand = inputValue;
            } else if (operator) {
                const result = performCalculation[operator](firstOperand, inputValue);
                displayValue = `${parseFloat(result.toFixed(7))}`;
                firstOperand = result;
            }

            waitingForSecondOperand = true;
            operator = nextOperator;
        }

        const performCalculation = {
            '/': (first, second) => first / second,
            '*': (first, second) => first * second,
            '+': (first, second) => first + second,
            '-': (first, second) => first - second,
            '=': (first, second) => second
        };

        function resetCalculator() {
            displayValue = '0';
            firstOperand = null;
            operator = null;
            waitingForSecondOperand = false;
        }
    }
});

