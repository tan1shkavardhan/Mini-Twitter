from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponseForbidden
from .models import Tweet
from .forms import TweetForm, UserRegistrationForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.db.models import Q


def index(request):
    tweets = Tweet.objects.all().order_by('-created_at')[:10]
    return render(request, 'index.html')

def tweet_list(request):
    tweets = Tweet.objects.all().order_by('-created_at')
    return render(request, 'tweet_list.html', {'tweets': tweets})

@login_required
def create_tweet(request):
    if request.method == "POST":
        form = TweetForm(request.POST, request.FILES)
        if form.is_valid():
            tweet = form.save(commit=False)
            tweet.user = request.user
            tweet.save()
            return redirect('tweet_list')
    else:
        form = TweetForm()
    return render(request, 'tweet_form.html', {'form': form})

@login_required
def edit_tweet(request, tweet_id):
    tweet = get_object_or_404(Tweet, pk=tweet_id)

    if tweet.user != request.user:
        return HttpResponseForbidden("You are not allowed to edit this tweet.")

    if request.method == "POST":
        form = TweetForm(request.POST, request.FILES, instance=tweet)
        if form.is_valid():
            form.save()
            return redirect('tweet_list')
    else:
        form = TweetForm(instance=tweet)

    return render(request, 'tweet_form.html', {'form': form})

@login_required
def delete_tweet(request, tweet_id):
    tweet = get_object_or_404(Tweet, pk=tweet_id)

    if tweet.user != request.user:
        return HttpResponseForbidden("You are not allowed to delete this tweet.")

    if request.method == "POST":
        tweet.delete()
        return redirect('tweet_list')

    return render(request, 'tweet_confirm_delete.html', {'tweet': tweet})

 

def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password1'])
            user.save()
            login(request,user)
            return redirect('tweet_list')        
    else:
        form = UserRegistrationForm()
    return render(request, 'registration/register.html', {'form':form})

def search(request):
    query=request.GET.get("q","").strip()
    results=[]

    if query:
        results= Tweet.objects.filter(
            Q(text__regex=rf"\b{query}\b"))
    else:
        results=[]

    return render(request,"search_results.html",{
        "query":query,
        "results":results
    })

