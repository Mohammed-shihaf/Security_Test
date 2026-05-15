# syntax=docker/dockerfile:1.7
FROM eclipse-temurin:17-jdk-alpine AS build
WORKDIR /build
RUN apk add --no-cache maven
COPY pom.xml .
RUN mvn -q -B dependency:go-offline -DskipTests || true
COPY src ./src
RUN mvn -q -B verify

FROM eclipse-temurin:17-jre-alpine AS runner
WORKDIR /app
RUN addgroup -g 1001 javaapp && adduser -u 1001 -G javaapp -D javaapp
COPY --from=build /build/target/catalog-service-*.jar /app/app.jar
USER javaapp
EXPOSE 8085
ENTRYPOINT ["java", "-jar", "/app/app.jar"]
