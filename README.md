# JSON.Lang

A small interpreted language that works using Lists of Tuples and Dicts, Entirely!

---
(warning: this doc is bad, if u see this, u r welcome to help and contribute!)
---
JSON.lang is a esoteric(maybe?) programming language designed around a *JSON+Tuples*-based instruction set to make you feel pain, with **functions, variable scopes, and expression evaluation**.

## == Syntax ==
JSON.lang programs are written as lists of tuples, where the first element in the instruction tuple is the instruction and the rest are arguments.  
The language has a **global scope** and **nested local scopes** for variables/functions.  

## Basic instructions:

* `var name value` – define or assign a variable.  
* `func name [params] [body]` – define a function with parameters and body.  
* `return value` – return a value from a function.  
* `if (condition) [then_body] [else_body]` – conditional execution.  
* `while (condition) [body]` – loop while condition is true.  
* `for var_name iterable [body]` – iterate over items.  
* `print *values` – output values.
* `input <datatype?>` - get user input, the datatype argument isnt required, but it used to convert the input to another datatype (like if you wanna take a number from the user input)
* `switch (anything has a value, should be inside of tuple) {<value>: [code..]} ... {<value>: [code..]} [default-block...]` - you already know what is that, another conditional execution
* `int/float/bool/str <also, anything has a value>` - return bool/str/int/float($the-given-value)
* Expressions: `+`, `-`, `*`, `/`, `%`, `==`, `!=`, `<`, `>`, `<=`, `>=`, `!->`, `and`, `or`, `not`, maybe more?
- note that `!->` means "not in", helpful with lists and idk what also

## == Examples ==

Hello world (printing a value):
```python
[
  ("print", "Hello World!")
]
```
Function definition and call:
```python
(
  ("func", "add", ["a", "b"], [
    ("return", ("+", "$a", "$b")
  ]),
  ("print", ("add", 5, 7))
)
```
Variable assignment:
```python
[
  ("var", "x", 42),
  ("print", "$x")
]
```
Conditional:
```python
[
  ("var", "x", 10),
  ("if", ("==", "$x", 10), [
    ("print", "x is ten")
  ], [
    ("print", "x is not ten")
  ])
]
```
Looping:
```python
[
  ("var", "i", 0),
  ("while", ("<", "$i", 5), [
    ("print", "$i"),
    ("var", "i", ("+", "$i", 1))
  ])
]
```
...more things (see tic_tac_toe.json.lang!)

## == Interpreter info ==
Well, this Language still unstable, but the official interpreter coded in Python <sadly :)

this is the official interpreter, if you can rewrite this language to another Programming Language like C, thank you!

---

> This FOSS product is licensed under the MIT License.
© 2025 Salah Refaae and Contributes
