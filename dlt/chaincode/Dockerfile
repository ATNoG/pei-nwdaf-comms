FROM gradle:8.11-jdk21 AS build
WORKDIR /chaincode
COPY build.gradle settings.gradle* ./
COPY src ./src
RUN gradle shadowJar --no-daemon -q

FROM eclipse-temurin:21-jre-alpine
WORKDIR /chaincode
COPY --from=build /chaincode/build/libs/chaincode.jar .
EXPOSE 7052
# CHAINCODE_SERVER_ADDRESS is set by docker-compose to run as CCAAS server
CMD ["java", "-jar", "chaincode.jar"]
