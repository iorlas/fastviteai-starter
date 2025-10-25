I'm not sure should we pull data from PIM into MedusaJS. I thought that we will pull it into UI only.
RakutenPay - I'm not sure it is available in Stripe, maybe we will need multiple payment gateways.

Also, functional modules like search and auth - we plan to rely on MedusaJS plugins as much as possible, which should significantly reduce the delivery time.

Voucherify points expiry - I think we can forget about it, but our system should enable us to spent such points as a part of checkout flow payment.

Also, in total, I'd be glad to make it in less than 8 month, ideally in 6.



Also, another goal for us - evaluate will MedusaJS work for us or there are some risks which are against us and we are better off evaluating something else.

I want to evaluate MedusaJS - you, an agent, should do it for me.

I see, but I think we can skip API compatibility layer - it is fine, we will update our
  UI (but it will also take time which we may need to take into account). Also, time-wise,
  we can cut some functional corners, but we want to go ive in 8 months tops - in 7 mpnths
  really 

Netsuite is already set up since we have it already integrated with a legacy system. 
Netsuite is slow for a fact, so we will need to sync it to/from medusajs, but use 
medusajs most of the time I think. Maybe stock syncup should be done more often. But 
anyway I want to follow the eCommerce best practices in retail. Also, we need all systems
 integrated for sure, all features mentioned implemented, but maybe some details could be
 cut out 


 mainly, I don't need microservices. separate engineer from a client side will implement
 some pieces using python as microservices: step up. Like, he did already skin check and 
products recommendations based on skin check quiz 


Success for us - deploying the system and migrating our customers with it in 7-8 months, while having much more stable system opposing the current legacy one
Failure - if payments wouldn't work, website will be too slow, internal operational team will get too confused with admin UI to make sense of orders. Or if system is more unstable (especially at checkout and payment workflow) than what we have (and right now we kinda got the system more or less stable, but there are too many random issues which are hard to figure out due to legacy complexity)
I don't think we can skip functionality in this time aside from details (like, subscription rescheduling to a certain date or maybe something else).
Budget - don't worry, it is based on the team composition I mentioned - so we have 2 UI, 1 lead, 1 deops, 2-3 backend engineers, 2 QA, this is it. Yes, we can purchase licenses like Shopify Plus or managed cloud MedusaJS. We will have some support from experienced guys along the road surely, don't worry about charging them tho. Yet, we want to make it in 8 months including migration.

Tech debt - I think we can tolerate it. We can release with bugs assuming that we will fix it in 1-2 months more.
Also, 7 months with 85% is ok, but it is ok to do it with 8 months.



Another large risk - how we will get RakutenPay integrated - directly or thru another gateway. Will multiple gateways play nicely in a system. exites a lot - that we will ditch the legacy, and system will be simplified. the company CTO said that he does not want to keep many engineers to manage this product - wanna do a new version, and be done with it - the company is not a software company, it is a retail company. My intuition tells that Shopify can be a huge problem since we need RakutenPay and credit cards, but AFAIK Stripe does not support RakutenPay so we might need to support 2 payment gateways at the same time which feels like might not be supported well. Maybe woocommerce is easier and much faster (CTO told that he made another strefront with it and it is fast, but he didn't implement all features details, and I'm afraid that if we will need to implement some details - we could face a blocker which could force us to fork some extentions and spend quite some time to make it work)

Correction - CTO said it is proven, but he is rushy to say so - storefront he built is much simpler. And we won't remove all engineers, I think in a year we will reduce it to 1 UI, 1 BE , 1 DevOps, 1 QA, or just 1 fullstack instead of 2 devs. Maybe DevOps will be ad-hoc. Also, I'm not sure about Stripe limitations, so we will need to research it. WooCommerce does not feel like a safe bet to me: php is dated like woocommerce and it's plugins. MedusaJS feels like a good modern yet risky option, yet mostly due to potential issues with Stripe. 

The main benefit is that the current legacy system is afwul and has hidden bugs which we are fighting every couple of days. No one wants to support it anymore. No one can, except some cheap companies.


Oh it is not stripe cannot handle dual gateways, it is the engine (medusajs, shopify, woocommerce). Also, we can get RakutenPay sandbox - since it is already integrated with a legacy codebase, so I'd expect access from a day 1. For Stripe/RakutenPay I'd expect MedusaJS to handle the checkout flow and create respective session. The rest of the risks feel valid. We will need to do researches to validate it and realize it is real or sorted.

Also, we are not sure neither WooCommerce supports dual gateways. 

RakutenPay is non-negotiatable, we need to integrate it ASAP to surface any risks, and it should be available by the release. Migration should also happen in parallel, but maybe we can claim that product is ready in 7 months, and then we will migrate it in a month, making it 8 months.

3 weeks for PoC.

