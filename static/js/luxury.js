/* luxury.js
   Adds polished scroll reveals, header behavior, button micro-interactions,
   and improves existing dropdown/slider UX. Works if GSAP is available, otherwise uses CSS classes.
*/

(function(){
  // Utilities
  function $q(sel, ctx){ return (ctx || document).querySelector(sel); }
  function $qa(sel, ctx){ return Array.from((ctx || document).querySelectorAll(sel)); }

  // Wait DOM ready
  document.addEventListener('DOMContentLoaded', function(){

    /* ---------- Header shrink on scroll ---------- */
    var header = $q('header.header');
    var lastScroll = 0;
    function onScrollHeader(){
      var st = window.scrollY || window.pageYOffset;
      if(st > 60){
        header.classList.add('scrolled');
      } else {
        header.classList.remove('scrolled');
      }
      lastScroll = st;
    }
    onScrollHeader();
    window.addEventListener('scroll', throttle(onScrollHeader, 40));

    /* ---------- GSAP entry animations (if available) ---------- */
    var hasGSAP = (typeof window.gsap !== 'undefined');

    if(hasGSAP){
      try{
        // nice hero reveal for any existing hero titles
        var heroTitles = $qa('.hero_slide_content h1, .hero h1, #hero-title');
        heroTitles.forEach(function(el,i){
          gsap.from(el, {y: 28, opacity: 0, duration: 0.9, delay: 0.12 + i*0.06, ease: "power3.out"});
        });

        // subtle parallax on hero backgrounds if present
        $qa('.hero_slide_background, .hero-image').forEach(function(bg){
          gsap.to(bg, {scale: 1.04, duration: 14, repeat: -1, yoyo: true, ease: "sine.inOut"});
        });
      }catch(e){
        console.warn('GSAP animation error', e);
      }
    } else {
      // add simple reveal class for CSS fallback if GSAP missing
      $qa('.card1, .card, .testimonials_item').forEach(function(c){
        c.classList.add('luxury-reveal');
      });
    }

    /* ---------- Intersection Observer: reveal elements ---------- */
    var io = new IntersectionObserver(function(entries, obs){
      entries.forEach(function(entry){
        if(entry.isIntersecting){
          var t = entry.target;
          if(hasGSAP){
            gsap.to(t, {y:0, opacity:1, duration:0.8, ease:"power3.out", overwrite:true});
          } else {
            t.style.opacity = 1;
            t.style.transform = 'translateY(0)';
            t.classList.add('visible');
          }
          obs.unobserve(t);
        }
      });
    }, {threshold: 0.12});

    // observe card1, card, testimonials, file-card
    $qa('.card1, .card, .testimonials_item, .file-card, .card1 .card-img-top, .course_box').forEach(function(el){
      el.style.opacity = 0;
      el.style.transform = 'translateY(18px)';
      io.observe(el);
    });

    /* ---------- Button hover micro interactions (GSAP if available) ---------- */
    $qa('.btn').forEach(function(btn){
      btn.style.transform = 'translateZ(0)';
      btn.addEventListener('mouseenter', function(){
        if(hasGSAP) gsap.to(btn, {y:-5, duration:0.22, ease:'power2.out'});
        else btn.style.transform = 'translateY(-4px)';
      });
      btn.addEventListener('mouseleave', function(){
        if(hasGSAP) gsap.to(btn, {y:0, duration:0.28, ease:'power2.out'});
        else btn.style.transform = 'translateY(0)';
      });
    });

    /* ---------- Dropdown accessibility (keeps your current behavior but improved) ---------- */
    document.querySelectorAll('.dropdown').forEach(function(dd){
      var toggle = dd.querySelector('.dropdown-toggle');
      var menu = dd.querySelector('.dropdown-menu');
      if(!toggle || !menu) return;

      toggle.addEventListener('click', function(ev){
        ev.preventDefault();
        var isOpen = menu.style.display === 'block';
        // close others
        document.querySelectorAll('.dropdown-menu').forEach(function(m){
          if(m !== menu) m.style.display = 'none';
        });
        menu.style.display = isOpen ? 'none' : 'block';
        menu.setAttribute('aria-expanded', (!isOpen).toString());
      });
    });

    // close when clicking outside
    document.addEventListener('click', function(e){
      if(!e.target.closest('.dropdown')) {
        document.querySelectorAll('.dropdown-menu').forEach(function(m){
          m.style.display = 'none';
        });
      }
    });

    /* ---------- Improve slider-container marquee (pause on hover + loop) ---------- */
    var marquee = document.querySelector('.slider-container .slider');
    if(marquee){
      // use CSS animation if already set; otherwise create a JS loop shifting transform left continuously
      var speed = 40; // pixels per second
      var rafId = null;
      var paused = false;
      var pos = 0;

      function step(){
        if(!paused){
          pos -= speed * (1/60);
          if(Math.abs(pos) >= marquee.scrollWidth/2){
            pos = 0;
          }
          marquee.style.transform = 'translateX(' + Math.round(pos) + 'px)';
        }
        rafId = requestAnimationFrame(step);
      }

      // duplicate content if short (create seamless loop)
      if(marquee.children.length > 0){
        // ensure content wide enough: duplicate once
        var clone = marquee.innerHTML;
        marquee.innerHTML += clone;
        marquee.style.display = 'flex';
        marquee.style.willChange = 'transform';
        marquee.addEventListener('mouseenter', function(){ paused = true; });
        marquee.addEventListener('mouseleave', function(){ paused = false; });
        requestAnimationFrame(step);
      }
    }

    /* ---------- small utility: throttle ---------- */
    function throttle(fn, wait){
      var time = Date.now();
      return function(){
        if((time + wait - Date.now()) < 0){
          fn();
          time = Date.now();
        }
      }
    }

    /* ---------- add prefers-reduced-motion respect ---------- */
    var reduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if(reduce){
      // disable intensive animations
      $qa('.hero_slide_background, .hero-image').forEach(function(el){
        el.style.transition = 'none';
        if(hasGSAP) try{ gsap.killTweensOf(el); } catch(e){}
      });
      $qa('.btn').forEach(function(b){ b.removeEventListener && b.removeEventListener('mouseenter', null); });
    }

    // end DOMContentLoaded
  });

})();
