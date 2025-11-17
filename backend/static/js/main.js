document.getElementById('add-event-form').addEventListener('submit', async (e)=>{
    e.preventDefault();
    const form = e.target;
    const data = {
        title: form.title.value,
        start_time: form.start_time.value,
        end_time: form.end_time.value
    };
    const res = await fetch('/event/create', {
        method:'POST',
        headers: {'Content-Type':'application/json'},
        body: JSON.stringify(data)
    });
    if(res.ok) location.reload();
});
