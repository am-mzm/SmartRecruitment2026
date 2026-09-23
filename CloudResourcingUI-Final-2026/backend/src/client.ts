import { PrismaClient } from "@prisma/client";

const prisma = new PrismaClient(); // Instantiate PrismaClient

export { prisma }; // Export PrismaClient instance