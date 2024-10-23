# FastAPI and ActivityPub Federated Digital Commerce Template

Accelerate federated digital commercial product development with this FastAPI/ActivityPub base project generator.

This project is for developers looking to build and maintain full-feature federated commercial progressive web applications using Python on the backend / Typescript on the frontend, and want the complex-but-routine aspects of auth 'n auth, and component and deployment configuration, taken care of, including interactive API documentation. 

This project started as [a fork](https://github.com/tiangolo/full-stack-fastapi-postgresql) of [a fork](https://github.com/whythawk/full-stack-fastapi-postgresql).

**NOTE**: this is still very much in early development, starting with the server. It is not yet of use.

## Core objectives

The template must offer a full-stack commercial app foundation, where the "digital product" here is a text payload which should be modified. Documentation will guide you through the code so you know where to begin adding in the specific implementation of your digital product.

Creators will have both a syndicated method for supporters to receive announcements about new products, and general purchasers to search a complete range of products and creators across all opting-in federated independent services.

The workflow will be:

-	Creators (ActivityPub Persons) generate profiles and populate it with information about themselves, including links to general social media,
- Creators produce a digital product which becomes a stand-alone ActivityPub actor (a Service),
-	Creators own their products and can associate other Person profiles with the work as co-creators,
-	Creators specify a price and revenue share with their co-creators, which generates a product link (e.g. Stripe links),
- Product links can be generated for regions or countries, and geolocked (if required),
-	On publication of the product, the Service profile goes live, and an announcement is published which specifies the work and a link for purchase (which links back to the Service profile where payment links can be found),
-	Payment triggers an event, which saves the product to the purchaser's profile (or, however you choose to implement this).

All ActivityPub Announcements (posts) are generated rather than produced by a person. That is, they are a consequence of creating and managing products.

Payment links are available only from Person and Service profile pages, and support the following:

-	One-time purchase
-	Subscription (e.g. to a Group where new Service products are regularly added)

This can permit a range of digital goods, e.g.:

- Long-form reports / articles (e.g. alt-Substack, alt-Tiny Letter),
- Crowd-funding of goods (e.g. alt-Kickstarter),
- Creator-support (e.g. alt-Patreon),
- Digital goods (e.g. pictures, pdfs, epubs, etc.)

What the digital good is, and how you serve it, is entirely up to you. This template lets you focus on that, while using a core platform that supports federation.
  
## Roadmap to first release

**Server**

- Docker compose script for all image dependencies (Postgres, PGAdmin, RabbitMQ, Flower, Redis)
- Reimplementation of OAuth2 for more comprehensive ActivityPub client requirements
- Basic account creation
- Bovine server integration to support:
  - Well-known endpoints
  - Follow, Post, etc
  - Syndicate, including to Mastodon and BlueSky
- User IP to country identity
- Moderation stack, including general admin blocks and reviews, user-based moderation, conditional publication process
- Commercial templates (starting with Stripe) for automatic product creation and purchase workflows
- Federated search allowing servers to share a searchable pool of Person and Service

**Client**

- Either modify an existing client (e.g. Phanpy or Elk), or build from scratch
- Support all server endpoints

## Template stack

This current stack contains only the server components:

- **Docker Compose** integration and optimization for local development.
- **Authentication** user management schemas, models, crud and apis already built, with OAuth2 JWT token support & default hashing. Offers _magic link_ authentication, with password fallback, with cookie management, including `access` and `refresh` tokens.
- [**FastAPI**](https://github.com/tiangolo/fastapi) backend with [Inboard](https://inboard.bws.bio/) one-repo Docker images, using Python 3.11:
  - **SQLAlchemy** version 2.0 support for models.
  - **Pydantic** version 2.7 for schemas.
  - **Bovine** for ActivityPub federation support.
  - **Metadata Schema** based on [Dublin Core](https://www.dublincore.org/specifications/dublin-core/dcmi-terms/#section-3) for inheritance.
  - **Common CRUD** support via generic inheritance.
  - **Standards-based**: Based on (and fully compatible with) the open standards for APIs: [OpenAPI](https://github.com/OAI/OpenAPI-Specification) and [JSON Schema](http://json-schema.org/).
  - **MJML** templates for common email transactions.
  - [**Many other features**]("https://fastapi.tiangolo.com/features/"): including automatic validation, serialization, interactive documentation, etc.
- **PostgreSQL** database.
- **PGAdmin** for PostgreSQL database management.
- **Celery** worker that can import and use models and code from the rest of the backend selectively.
- **Flower** for Celery jobs monitoring.
- **RabbitMQ** for enquing asyncronous tasks, as well as ActivityPub federation tasks.
- **Redis** for caching API queries.
- Load balancing with **Traefik**, so you can have both under the same domain, separated by path, but served by different containers.
- Traefik integration, including Let's Encrypt **HTTPS** certificates automatic generation.

## How to use it

These are the documentation of the forked template. These will be revised to serve this template:

- [Getting started](./docs/getting-started.md)
- [Development and installation](./docs/development-guide.md)
- [Deployment for production](./docs/deployment-guide.md)
- [Authentication and magic tokens](./docs/authentication-guide.md)
- [Websockets for interactive communication](./docs/websocket-guide.md)

## Help needed

This is a huge undertaking, and the roadmap itself needs development (both what's on it, and implementing it). Plus, tests and documentation required. For now, just contact me direct if you want to help so we can parcel out the work, but dive in.

## License

This project is licensed under the terms of the MIT license.
