---
layout: post
title: Creating a Conditional React Hook
date: 2019-09-13
categories:
  - programming
tags:
  - react
  - reactjs
  - hooks
image: /assets/images/react.png
---

After seeing that the React team have been encouraging people to start using hooks for future development over the class based approach that has been used for stateful components previously, I decided to check them out.

My first thoughts were that the new approach is **really** awesome. Much less boilerplate code and the ability to share logic between different components easily - what's not to love?

I quickly jumped in to trying to use them, and almost as quickly hit a dead end. I was trying to create a form that would:

1. Load data from a remote server and populate a form with the result
2. Call an API to save the data back when the user hits the save button

The first point went smoothly, but the second? Not so much. One of the rules that has to be followed when using hooks is that they all must be called in the top level of the function.

What I mean by this, is that anything that accepts a callback, such as `useEffect` cannot contain hook invocations. They all must appear in the main function of the hook, ensuring that the same number of hooks are invoked every time a re-render occurs.

Why is this a problem? Well, I was trying to invoke the hook when the user clicks a button, which means the first render only calls one hook (to load the remote data) but the render after the user clicks the button was then calling two hooks.

The solution to this was incredibly simple, but didn't click straight away. That solution being - I could create a flag in my hook to indicate whether or not to actually execute the action. Doing this would ensure that the same number of hooks are called every time, but it'd only execute the action when the flag is changed to indicate it should.

Below is an example of my hook, with some implementation replaced with some mock code for the sake of keeping it simple.

```jsx
import React, { useState, useEffect } from 'react'

function useApi ({ endpoint, method, body, shouldExecute }) {
  const [result, setResult] = useState(null)
  const [executing, setExecuting] = useState(false)
  const [hasError, setHasError] = useState(false)

  if (shouldExecute) {
    setExecuting(true)
  }

  const executeRequest = async () => {
    try {
      const res = await ApiExample.call(endpoint, method, body)
      setResult(res)
    } catch (error) {
      setHasError(true)
    }

    setExecuting(false)
  }

  useEffect(() => {
    if (shouldExecute) {
      executeRequest()
    }
  }, [shouldExecute])

  return { executing, hasError, result }
}

export default useApi
```

The purpose of this hook is to be able to specify the API endpoint, HTTP method and body and get an object back that indicates:

- Whether the task is executing (`executing`)
- Whether an error occurred making the request (`hasError`)
- The result of the request, if successful (`result`)

If we were *not* to pass the `shouldExecute` value and use it and instead invoke `executeRequest` immediately inside the callback of `useEffect`, the HTTP request would be sent to the API pretty much instantly after the hook is invoked. Whilst this is fine for loading data, this was not sufficient for my use case of wanting to execute a request upon clicking a save button. Enter - the `shouldExecute` value.

By adding this extra flag, `useEffect` can be configured to be dependent on `shouldExecute` (as can be seen in the second argument to `useEffect`). This means that every time `shouldExecute` changes - the `useEffect` callback is invoked (you can probably see where this is now going).

Now that the `useApi` hook will only make the AJAX request based on the flag that we can bind a value to in its consumer, we can invoke it twice at the start of the consuming hook like this:

```jsx
const ApiWrapper = () => {
  const [shouldSave, setShouldSave] = useState(false)

  const a = useApi({
    endpoint: '/load-data',
    method: 'GET',
    shouldExecute: true
  })

  const b = useApi({
    endpoint: '/save-data',
    method: 'POST',
    body: { foo: 'bar' },
    shouldExecute: shouldSave
  })

  if (shouldSave && !b.executing) {
    setShouldSave(false)
  }

  return (
    <div>
      <span>{a.result}</span>
      <button onClick={() => setShouldSave(true)}>Save</button>
    </div>
  )
}
```

In this example, `a` will hold the data that would then populate a form (in this case just dumping it into a `span` to keep things concise) and `b` will hold the result of the save operation.

On the first render of `ApiWrapper`, the `useApi` hook will be called twice and the results assigned to `a` and `b`. As you can see in the assignment of `b`, the `shouldExecute` property is bound to the value of `shouldSave`, which is only set to `true` once the user clicks the button.

There is also a check to reset the flag, if `shouldSave` is `true`. If it is `true`, the user has previously clicked the button, and if `b.executing` is `false`, then that would mean the task in the `useApi` hook is now finished and we can reset the value of `shouldSave`.

It's a bit different to how one would normally approach this, but overall, it actually makes the code even more concise and easy to read, so I'd still say it's worth adapting to this type of approach.

If you need more information on how `useEffect` works and the general changes that have been introduced with hooks, make sure to check out the official documentation at [https://reactjs.org/docs/hooks-intro.html](https://reactjs.org/docs/hooks-intro.html)
